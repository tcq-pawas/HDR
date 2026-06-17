from django.shortcuts import redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .auth_utils import get_user_role, get_role_based_redirect_url


class SmartDashboardRedirectView(LoginRequiredMixin, View):
    """
    Smart dashboard entry point that redirects users based on their group membership
    URL: /dashboard/ - acts as a universal dashboard entry point
    """
    
    def get(self, request, *args, **kwargs):
        """Redirect user to their appropriate dashboard based on group membership"""
        user = request.user
        
        # Get user's role from group membership
        role = get_user_role(user)
        
        if role:
            # User has a valid role, redirect to appropriate dashboard
            redirect_url = get_role_based_redirect_url(user)
            return redirect(redirect_url)
        else:
            # User is authenticated but has no role groups
            # Redirect to a role assignment page or show an error
            from django.contrib import messages
            messages.error(
                request, 
                "Your account is not assigned to any user group. "
                "Please contact an administrator to get proper access."
            )
            return redirect('auth:unauthorized')


class RoleBasedDashboardMixin:
    """
    Mixin to enforce strict role-based access control on dashboard views
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth:login')
        
        # Get user's role from group membership
        user_role = get_user_role(request.user)
        
        # Check if user has any role assigned
        if not user_role:
            from django.contrib import messages
            messages.error(
                request, 
                "Your account is not assigned to any user group. "
                "Please contact an administrator to get proper access."
            )
            return redirect('auth:unauthorized')
        
        # Check if this view allows the user's role
        if not self.has_role_access(user_role):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                f"Access denied. You don't have permission to access this dashboard. "
                f"Your role: {user_role or 'None'}"
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_role_access(self, user_role):
        """
        Override in subclasses to define which roles can access this view
        Returns True if user_role is allowed, False otherwise
        """
        raise NotImplementedError("Subclasses must implement has_role_access method")


class AdminDashboardMixin(RoleBasedDashboardMixin):
    """Mixin for admin-only dashboard access"""
    
    def has_role_access(self, user_role):
        return user_role == 'admin'


class CustomerDashboardMixin(RoleBasedDashboardMixin):
    """Mixin for customer-only dashboard access"""
    
    def has_role_access(self, user_role):
        return user_role == 'customer'


class InvestorDashboardMixin(RoleBasedDashboardMixin):
    """Mixin for investor-only dashboard access"""
    
    def has_role_access(self, user_role):
        return user_role == 'investor'


class AgentDashboardMixin(RoleBasedDashboardMixin):
    """Mixin for agent-only dashboard access"""
    
    def has_role_access(self, user_role):
        return user_role in ['agent', 'owner']
