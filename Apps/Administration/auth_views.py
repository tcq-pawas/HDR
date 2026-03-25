from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import JsonResponse
from .auth_utils import get_role_based_redirect_url, get_dashboard_context, get_user_role


class CustomLoginView(TemplateView):
    """Custom login view with role-based redirection"""
    template_name = 'auth/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_role_based_redirect_url(request.user))
        
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Get user role and redirect to appropriate dashboard
                redirect_url = get_role_based_redirect_url(user)
                
                # Add success message
                role = get_user_role(user)
                messages.success(request, f"Welcome back! Redirecting to your {role} dashboard.")
                
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
            messages.error(request, "Please correct the errors below.")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
        
        return render(request, self.template_name, {'form': form})


class CustomLogoutView(TemplateView):
    """Custom logout view"""
    template_name = 'auth/logout.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            role = get_user_role(request.user)
            logout(request)
            messages.info(request, f"You have been logged out from your {role} dashboard.")
        
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            role = get_user_role(request.user)
            logout(request)
            messages.info(request, f"You have been logged out from your {role} dashboard.")
        
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


def unauthorized_access(request, exception):
    """Custom view for unauthorized access"""
    from django.core.exceptions import PermissionDenied
    return render(request, 'auth/unauthorized.html', status=403)
