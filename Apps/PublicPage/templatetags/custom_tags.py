from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.simple_tag
def get_profile_image(user):
    """Get profile image URL based on user's group"""
    if not user or not user.is_authenticated:
        return None
    
    # Check user groups and return appropriate profile image
    if user.groups.filter(name='Agent').exists():
        if hasattr(user, 'agent_profile') and user.agent_profile.profile_image:
            return user.agent_profile.profile_image.url
    elif user.groups.filter(name='Customer').exists():
        if hasattr(user, 'customer_profile') and user.customer_profile.profile_picture:
            return user.customer_profile.profile_picture.url
    elif user.groups.filter(name='Investor').exists():
        if hasattr(user, 'investor_profile') and user.investor_profile.profile_image:
            return user.investor_profile.profile_image.url
    elif user.groups.filter(name='Administration').exists():
        # Admin profile doesn't have profile_image field, return None
        pass
    
    return None


@register.simple_tag
def get_profile_url(user):
    """Get profile URL based on user's group"""
    if not user or not user.is_authenticated:
        return '#'
    
    # Check user groups and return appropriate profile URL
    if user.groups.filter(name='Agent').exists():
        return '/agent/settings/'
    elif user.groups.filter(name='Customer').exists():
        return '/customer/profile/'
    elif user.groups.filter(name='Investor').exists():
        return '/investor/profile/'
    elif user.groups.filter(name='Administration').exists():
        return f'/admin/users/{user.id}/'
    
    return '#'
