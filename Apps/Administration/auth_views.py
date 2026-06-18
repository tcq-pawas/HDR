from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .auth_utils import get_role_based_redirect_url, get_dashboard_context, get_user_role
from Apps.Customer.forms import CustomerRegistrationForm
from .forms import PartnerRegistrationForm


class CustomLoginView(TemplateView):
    """Custom login view with role-based redirection"""
    template_name = 'auth/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_role_based_redirect_url(request.user))
        
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')
        
        from django.core.cache import cache
        from Apps.Administration.models import SystemSettings
        
        try:
            max_attempts_setting = SystemSettings.objects.filter(setting_key='MAX_LOGIN_ATTEMPTS').first()
            max_attempts = int(max_attempts_setting.setting_value) if max_attempts_setting and max_attempts_setting.setting_value else 5
        except (ValueError, AttributeError):
            max_attempts = 5
            
        cache_key = f'login_attempts_{username}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= max_attempts:
            error_msg = "Maximum login attempts exceeded. Please try after 1 hour or reset your password and try again."
            messages.error(request, error_msg)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': {'__all__': [error_msg]}})
            
            form = AuthenticationForm(request)
            return render(request, self.template_name, {'form': form})
            
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            if user is not None:
                # Clear failed attempts on successful login
                cache.delete(cache_key)
                
                login(request, user)
                
                # Log login activity and location
                lat = request.POST.get('latitude')
                lng = request.POST.get('longitude')
                description = "User logged in."
                if lat and lng:
                    location_str = f"Latitude {lat}, Longitude {lng}"
                    try:
                        import urllib.request
                        import json
                        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
                        req = urllib.request.Request(url, headers={'User-Agent': 'HeyDayRealty/1.0'})
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
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Get user role and redirect to appropriate dashboard
                redirect_url = get_role_based_redirect_url(user)
                role = get_user_role(user)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': redirect_url,
                        'role': role
                    })
                
                return redirect(redirect_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Increment failed attempts
            attempts += 1
            cache.set(cache_key, attempts, timeout=3600)  # 1 hour timeout
            
            if attempts >= max_attempts:
                error_msg = "Maximum login attempts exceeded. Please try after 1 hour or reset your password and try again."
                # Clear previous messages if any
                list(messages.get_messages(request))
                messages.error(request, error_msg)
            else:
                if form.non_field_errors():
                    for error in form.non_field_errors():
                        messages.error(request, error)
                else:
                    messages.error(request, f"Invalid username or password. {max_attempts - attempts} attempts remaining.")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = form.errors if attempts < max_attempts else {'__all__': [error_msg]}
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        
        return render(request, self.template_name, {'form': form})


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
            login(request, user)
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
            role_display = dict(PartnerRegistrationForm.ROLE_CHOICES).get(form.cleaned_data['role'])
            
            # Send 'Under Review' email
            html_message = f"""
            <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="background: linear-gradient(135deg, #0F766E 0%, #115E59 100%); padding: 30px 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 1px;">🌱 HeyDay Realty</h1>
                </div>
                <div style="padding: 40px 30px; background-color: #ffffff;">
                    <h2 style="color: #1F2937; margin-top: 0; font-size: 22px;">Account Under Review</h2>
                    <p style="color: #4B5563; font-size: 16px; line-height: 1.6;">Hello <strong>{user.first_name}</strong>,</p>
                    <p style="color: #4B5563; font-size: 16px; line-height: 1.6;">Thank you for registering as a <strong>{role_display}</strong> with HeyDay Realty. We are excited to have you on board!</p>
                    <div style="background-color: #F3F4F6; border-left: 4px solid #FBBF24; padding: 15px 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                        <p style="color: #4B5563; font-size: 15px; margin: 0; line-height: 1.5;">Your account is currently under review by our administration team. You will receive another email with your login details once your account has been approved.</p>
                    </div>
                    <p style="color: #4B5563; font-size: 16px; line-height: 1.6;">Best regards,<br><strong style="color: #0F766E;">HeyDay Realty Team</strong></p>
                </div>
                <div style="background-color: #F9FAFB; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9CA3AF; font-size: 13px; margin: 0;">&copy; 2026 HeyDay Realty. All rights reserved.</p>
                </div>
            </div>
            """
            send_mail(
                subject='Account Under Review - HeyDay Realty',
                message=f'Hello {user.first_name},\n\nThank you for registering as a {role_display} with HeyDay Realty.\n\nYour account is currently under review by our administration team. You will receive another email with your login details once your account has been approved.\n\nBest regards,\nHeyDay Realty Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,
            )
            
            return render(request, 'auth/registration_pending.html', {'email': user.email})
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
