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
        password = request.POST.get('password', '')
        
        # Check if user is suspended/inactive first
        from django.contrib.auth.models import User
        user_check = User.objects.filter(username=username).first()
        if user_check and not user_check.is_active:
            if user_check.check_password(password):
                error_msg = "Your account is suspended."
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
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Get user role and redirect to appropriate dashboard
                redirect_url = get_role_based_redirect_url(user)
                role = get_user_role(user)
                
                if role == 'agent':
                    from Apps.Subscriptions.utils import auto_assign_free_plan
                    auto_assign_free_plan(user)
                
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
