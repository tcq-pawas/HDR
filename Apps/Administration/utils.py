"""
Utility functions for Contact Inquiry API
Handles IP address extraction, user-agent parsing, and context generation
"""

import logging
from django.conf import settings


logger = logging.getLogger('contact_inquiry_api')


def get_client_ip(request):
    """
    Extracts the client's IP address from the request
    
    Args:
        request: The HTTP request object
    
    Returns:
        str: The client's IP address or None if not found
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Extracts the user agent string from the request
    
    Args:
        request: The HTTP request object
    
    Returns:
        str: The user agent string or empty string if not found
    """
    return request.META.get('HTTP_USER_AGENT', '')


def get_source_url(request):
    """
    Extracts the source URL from the request (referer header)
    
    Args:
        request: The HTTP request object
    
    Returns:
        str: The source URL or empty string if not found
    """
    return request.META.get('HTTP_REFERER', '')


def get_browser_info(user_agent):
    """
    Parses user agent string to extract browser information
    
    Args:
        user_agent: The user agent string
    
    Returns:
        str: Simplified browser information
    """
    if not user_agent:
        return "Unknown"
    
    user_agent = user_agent.lower()
    
    browser_map = {
        'chrome': 'Chrome',
        'firefox': 'Firefox',
        'safari': 'Safari',
        'edge': 'Edge',
        'opera': 'Opera',
        'msie': 'Internet Explorer',
        'trident': 'Internet Explorer',
    }
    
    for key, value in browser_map.items():
        if key in user_agent:
            return value
    
    return "Unknown Browser"


def generate_email_context(inquiry, website_config):
    """
    Generates the context dictionary for email templates
    
    Args:
        inquiry: The ContactInquiry model instance
        website_config: The website configuration dictionary
    
    Returns:
        dict: Context dictionary for email template
    """
    context = {
        'company_name': website_config.get('company_name', ''),
        'full_name': inquiry.full_name,
        'phone_number': inquiry.phone_number,
        'email': inquiry.email,
        'message': inquiry.message,
        'website': inquiry.website,
        'ip_address': inquiry.ip_address or 'Not available',
        'browser': get_browser_info(inquiry.user_agent),
        'submitted_at': inquiry.created_at,
        'source_url': inquiry.source_url or 'Not available',
    }
    
    # Add optional fields if they exist
    if hasattr(inquiry, 'subject') and inquiry.subject:
        context['subject'] = inquiry.subject
    
    if hasattr(inquiry, 'preferred_contact_method') and inquiry.preferred_contact_method:
        context['preferred_contact_method'] = inquiry.preferred_contact_method
    
    if hasattr(inquiry, 'property_type') and inquiry.property_type:
        context['property_type'] = inquiry.property_type
    
    if hasattr(inquiry, 'preferred_location') and inquiry.preferred_location:
        context['preferred_location'] = inquiry.preferred_location
    
    if hasattr(inquiry, 'budget_range') and inquiry.budget_range:
        context['budget_range'] = inquiry.budget_range
    
    if hasattr(inquiry, 'area_size') and inquiry.area_size:
        context['area_size'] = inquiry.area_size
    
    return context


def sanitize_input(value):
    """
    Sanitizes user input to prevent XSS attacks
    
    Args:
        value: The input value to sanitize
    
    Returns:
        str: Sanitized string
    """
    if value is None:
        return ''
    
    import html
    return html.escape(str(value))
