from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .auth_utils import get_role_based_redirect_url, get_dashboard_context, get_user_role
from .backends import get_user_by_login_identifier
from Apps.Customer.forms import CustomerRegistrationForm
from .forms import PartnerRegistrationForm, CustomAuthenticationForm


class CustomLoginView(TemplateView):
    """Custom login view with role-based redirection"""
    template_name = 'auth/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_role_based_redirect_url(request.user))
        
        form = CustomAuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        from django.core.cache import cache
        from Apps.Administration.models import SystemSettings
        from Apps.Administration.backends import AUTH_BACKEND_PATH
        identifier = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        try:
            max_attempts_setting = SystemSettings.objects.filter(setting_key='MAX_LOGIN_ATTEMPTS').first()
            max_attempts = int(max_attempts_setting.setting_value) if max_attempts_setting and max_attempts_setting.setting_value else 5
        except (ValueError, AttributeError):
            max_attempts = 5

        cache_key = f'login_attempts_{identifier.lower()}'
        attempts = cache.get(cache_key, 0)

        form = CustomAuthenticationForm(request, data={
            'username': identifier,
            'password': password,
        })

        def render_login(error_msg=None):
            if error_msg:
                messages.error(request, error_msg)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [error_msg]} if error_msg else form.errors,
                })
            return render(request, self.template_name, {'form': form})

        if attempts >= max_attempts:
            return render_login(
                "Maximum login attempts exceeded. Please try after 1 hour or reset your password and try again."
            )

        # Resolve user from username / email / profile mobile, then verify password
        user = get_user_by_login_identifier(identifier)
        # import pdb; pdb.set_trace()
        if user and not user.is_active and user.check_password(password):
            from Apps.Organization.models import AgentInvitation
            has_pending_invite = AgentInvitation.objects.filter(
                agent=user, status=AgentInvitation.Status.PENDING
            ).exists()
            if has_pending_invite:
                return render_login(
                    "Your invitation is still pending. Please complete account setup using your invitation link."
                )
            return render_login("Your account is suspended.")

        if user and user.is_active and user.check_password(password):
            cache.delete(cache_key)
            login(request, user, backend=AUTH_BACKEND_PATH)

            lat = request.POST.get('latitude')
            lng = request.POST.get('longitude')
            description = "User logged in."
            if lat and lng:
                location_str = f"Latitude {lat}, Longitude {lng}"
                try:
                    import urllib.request
                    import json
                    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'HHectare/1.0'})
                    with urllib.request.urlopen(req, timeout=3) as response:
                        data = json.loads(response.read().decode())
                        if 'display_name' in data:
                            location_str = data['display_name']
                except Exception:
                    pass
                description += f" Location: {location_str}"

            from Apps.Administration.models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action_type='login',
                module='authentication',
                description=description,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )

            redirect_url = get_role_based_redirect_url(user)
            role = get_user_role(user)

            if role == 'agent':
                from Apps.Subscriptions.utils import auto_assign_free_plan
                auto_assign_free_plan(user)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': redirect_url,
                    'role': role,
                })

            return redirect(redirect_url)

        # Failed login
        attempts += 1
        cache.set(cache_key, attempts, timeout=3600)

        if attempts >= max_attempts:
            error_msg = "Maximum login attempts exceeded. Please try after 1 hour or reset your password and try again."
        else:
            remaining = max_attempts - attempts
            error_msg = (
                f"Invalid email, phone, username, or password. {remaining} attempts remaining."
            )

        return render_login(error_msg)

class CustomerRegistrationView(TemplateView):
    """Customer registration view"""
    template_name = 'auth/register_customer.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_role_based_redirect_url(request.user))
            
        form = CustomerRegistrationForm()
        return render(request, self.template_name, {'form': form})
        
    def post(self, request, *args, **kwargs):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import authenticate
            user = authenticate(username=user.username, password=request.POST.get('password1'))
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(get_role_based_redirect_url(user))
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
            return render(request, self.template_name, {'form': form})


class PartnerRegistrationView(TemplateView):
    """Partner (Agent/Investor) registration view"""
    template_name = 'auth/register_partner.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_role_based_redirect_url(request.user))
            
        form = PartnerRegistrationForm()
        return render(request, self.template_name, {'form': form})
        
    def post(self, request, *args, **kwargs):
        form = PartnerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(username=user.username, password=request.POST.get('password1'))
            if user:
                login(request, user, backend='Apps.Administration.backends.EmailOrUsernameModelBackend')
                
                role = form.cleaned_data.get('role')
                if role == 'agent':
                    from Apps.Subscriptions.utils import auto_assign_free_plan
                    auto_assign_free_plan(user)
                    
                return redirect(get_role_based_redirect_url(user))
            else:
                return redirect('login')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
            return render(request, self.template_name, {'form': form})


class CustomLogoutView(TemplateView):
    """Custom logout view"""
    template_name = 'auth/logout.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        
        return redirect('login')


class RoleBasedDashboardView(TemplateView):
    """Base view for role-based dashboards"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Get user role
        user_role = get_user_role(request.user)
        
        # Check if user has the required role for this dashboard
        if not self.check_role_access(user_role):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to access this dashboard.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def check_role_access(self, user_role):
        """Override in subclasses to implement role-specific access control"""
        return True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_dashboard_context(self.request.user))
        return context


def unauthorized_access(request, exception=None):
    """View for 403 Forbidden errors"""
    return render(request, 'auth/unauthorized.html', status=403)


from django.views import View
from django.utils import timezone
from Apps.Administration.models import UserVerification
from Apps.Administration.utils import generate_otp, send_msg91_otp, send_email_otp

class RequestOTPView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
            
        verification_type = request.POST.get('type')  # 'email' or 'mobile'
        
        # Get or create UserVerification
        verification, created = UserVerification.objects.get_or_create(user=request.user)
        
        otp = generate_otp()
        verification.otp_created_at = timezone.now()
        
        if verification_type == 'email':
            verification.email_otp = otp
            verification.save()
            success = send_email_otp(request.user.email, otp)
            if success:
                return JsonResponse({'success': True, 'message': 'OTP sent to email'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send email'}, status=500)
                
        elif verification_type == 'mobile':
            # Check if phone number is provided or exists
            phone = request.POST.get('phone') or verification.phone_number
            if not phone:
                return JsonResponse({'success': False, 'message': 'Phone number required'}, status=400)
            
            verification.phone_number = phone
            verification.mobile_otp = otp
            verification.save()
            
            success = send_msg91_otp(phone, otp)
            if success:
                return JsonResponse({'success': True, 'message': 'OTP sent via SMS'})
            else:
                return JsonResponse({'success': False, 'message': 'Failed to send SMS'}, status=500)
                
        return JsonResponse({'success': False, 'message': 'Invalid verification type'}, status=400)


class VerifyOTPView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
            
        verification_type = request.POST.get('type')  # 'email' or 'mobile'
        submitted_otp = request.POST.get('otp')
        
        try:
            verification = UserVerification.objects.get(user=request.user)
        except UserVerification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No pending verification'}, status=400)
            
        # Check OTP expiration (e.g., 10 minutes)
        if verification.otp_created_at:
            delta = timezone.now() - verification.otp_created_at
            if delta.total_seconds() > 600:
                return JsonResponse({'success': False, 'message': 'OTP expired'}, status=400)
        
        if verification_type == 'email':
            if verification.email_otp == submitted_otp:
                verification.is_email_verified = True
                verification.email_otp = None
                verification.save()
                return JsonResponse({'success': True, 'message': 'Email verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP'}, status=400)
                
        elif verification_type == 'mobile':
            if verification.mobile_otp == submitted_otp:
                verification.is_mobile_verified = True
                verification.mobile_otp = None
                verification.save()
                return JsonResponse({'success': True, 'message': 'Mobile number verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP'}, status=400)
                
        return JsonResponse({'success': False, 'message': 'Invalid verification type'}, status=400)
