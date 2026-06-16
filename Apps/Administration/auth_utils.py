from django.contrib.auth.models import User, Group
from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.db import models
from functools import wraps


def get_user_role(user):
    """Get the primary role of a user based on their group membership"""
    if not user.is_authenticated or not user.pk:
        return None
    
    # Check in order of priority: admin > investor > customer > agent
    if user.is_superuser or user.groups.filter(name='admin').exists():
        return 'admin'
    elif user.groups.filter(name='owner').exists():
        return 'owner'
    elif user.groups.filter(name='investor').exists():
        return 'investor'
    elif user.groups.filter(name='customer').exists():
        return 'customer'
    elif user.groups.filter(name='agent').exists():
        return 'agent'
    else:
        return None


def assign_user_group(user, role):
    """Assign user to appropriate group based on role"""
    if role not in ['customer', 'investor', 'admin', 'agent', 'owner']:
        raise ValueError("Role must be one of: customer, investor, admin, agent, owner")
    
    # Remove from all role groups first
    role_groups = Group.objects.filter(name__in=['customer', 'investor', 'admin', 'agent', 'owner'])
    user.groups.remove(*role_groups)
    
    # Add to the specified group
    group, created = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    
    # If admin, also grant staff status
    if role == 'admin':
        user.is_staff = True
        user.save()
    
    return group


def role_required(allowed_roles=None):
    """
    Decorator to ensure user has required role
    Usage: @role_required(['customer', 'investor'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('auth:login')
            
            user_role = get_user_role(request.user)
            if not user_role:
                from django.contrib import messages
                messages.error(
                    request, 
                    "Your account is not assigned to any user group. "
                    "Please contact an administrator to get proper access."
                )
                return redirect('auth:unauthorized')
            
            if allowed_roles and user_role not in allowed_roles:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied(f"Access denied. Required role: {', '.join(allowed_roles)}")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_role_based_redirect_url(user):
    """Get the appropriate dashboard URL for a user based on their role"""
    role = get_user_role(user)
    
    if role == 'admin':
        return reverse('admin_dash:dashboard')
    elif role == 'investor':
        return reverse('investor:dashboard')
    elif role == 'customer':
        return reverse('customer:dashboard')
    elif role == 'agent' or role == 'owner':
        return reverse('agent:dashboard')
    else:
        return reverse('auth:unauthorized')  # Fallback to unauthorized page


def create_user_with_role(username, email, password, role, **extra_fields):
    """Create a new user and assign them to a role group"""
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        **extra_fields
    )
    
    assign_user_group(user, role)
    return user


def has_role_permission(user, required_role):
    """Check if user has the required role"""
    user_role = get_user_role(user)
    return user_role == required_role


def agent_required(view_func):
    """
    Decorator to ensure user is an agent
    Usage: @agent_required
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.decorators import login_required
            return login_required(view_func)(request, *args, **kwargs)
        
        user_role = get_user_role(request.user)
        if user_role not in ['agent', 'owner']:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Access denied. This page is only accessible to agents and owners.")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_api(view_func):
    """
    Decorator for API views to ensure user is an admin
    Usage: @admin_required_api
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed("Authentication required.")
        
        user_role = get_user_role(request.user)
        if user_role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return view_func(request, *args, **kwargs)
    return wrapper


class RoleRequiredMixin:
    """Mixin to enforce role-based access in class-based views"""
    required_roles = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth:login')
        
        user_role = get_user_role(request.user)
        if not user_role:
            from django.contrib import messages
            messages.error(
                request, 
                "Your account is not assigned to any user group. "
                "Please contact an administrator to get proper access."
            )
            return redirect('auth:unauthorized')
        
        if self.required_roles and user_role not in self.required_roles:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(f"Access denied. Required role: {', '.join(self.required_roles)}")
        
        return super().dispatch(request, *args, **kwargs)


def get_dashboard_context(user):
    """Get dashboard context based on user role"""
    role = get_user_role(user)
    context = {
        'user_role': role,
        'user': user,
    }
    
    if role == 'customer':
        from Apps.Customer.models import CustomerProfile, Inquiry, SavedProperty
        from Apps.PublicPage.models import Property
        
        try:
            profile = CustomerProfile.objects.get(user=user)
            context['profile'] = profile
        except CustomerProfile.DoesNotExist:
            context['profile'] = None
        
        context['inquiry_count'] = Inquiry.objects.filter(customer=user).count()
        context['saved_properties_count'] = SavedProperty.objects.filter(customer=user).count()
        context['recent_inquiries'] = Inquiry.objects.filter(customer=user).order_by('-created_at')[:5]
        
    elif role == 'investor':
        from Apps.Investor.models import InvestorProfile, Investment, InvestmentListing
        
        try:
            profile = InvestorProfile.objects.get(user=user)
            context['profile'] = profile
        except InvestorProfile.DoesNotExist:
            context['profile'] = None
        
        context['investment_count'] = Investment.objects.filter(investor=user).count()
        context['total_invested'] = Investment.objects.filter(
            investor=user, status='confirmed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Get available investment listings
        context['available_listings'] = InvestmentListing.objects.filter(
            status='active'
        ).order_by('-created_at')[:5]
        
    elif role == 'admin':
        from django.contrib.auth.models import User
        from Apps.Customer.models import CustomerProfile, Inquiry
        from Apps.Investor.models import InvestorProfile, Investment
        from Apps.PublicPage.models import Property
        
        context['total_users'] = User.objects.count()
        context['total_customers'] = CustomerProfile.objects.count()
        context['total_investors'] = InvestorProfile.objects.count()
        context['total_properties'] = Property.objects.count()
        context['pending_inquiries'] = Inquiry.objects.filter(status='pending').count()
        context['active_investments'] = Investment.objects.filter(status='confirmed').count()
    
    return context
