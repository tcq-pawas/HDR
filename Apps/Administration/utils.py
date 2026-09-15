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


import random
import requests
from django.core.mail import send_mail

def generate_otp(length=6):
    """Generates a numeric OTP of given length."""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def send_msg91_otp(phone_number, otp):
    """
    Sends an OTP via MSG91 SendOTP API.
    Falls back to legacy API if template-based fails.
    """
    import pdb
    pdb.set_trace()
    auth_key = settings.MSG91_AUTH_KEY
    template_id = settings.MSG91_TEMPLATE_ID

    if not auth_key:
        logger.warning(f"MSG91 auth key missing. Would have sent OTP {otp} to {phone_number}")
        return False

    # Clean the phone number (ensure country code is present, defaults to 91)
    cleaned_phone = phone_number.replace("+", "").strip()
    if len(cleaned_phone) == 10:
        cleaned_phone = f"91{cleaned_phone}"

    # Try template-based OTP first (if template_id is available)
    if template_id:
        url = "https://control.msg91.com/api/v5/otp"
        headers = {
            "authkey": auth_key,
            "Content-Type": "application/json"
        }
        payload = {
            "template_id": template_id,
            "mobile": cleaned_phone,
            "otp": otp
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            logger.info(f"MSG91 Template API Response: {response.status_code}, Body: {response.text}")
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('type') == 'success':
                    return True
        except Exception as e:
            logger.warning(f"MSG91 Template API Failed: {str(e)}, trying legacy API")

    # Fallback to legacy OTP API (no template required)
    url = "https://control.msg91.com/api/v5/otp"
    headers = {
        "authkey": auth_key,
        "Content-Type": "application/json"
    }
    payload = {
        "authkey": auth_key,
        "mobile": cleaned_phone,
        "otp": otp,
        "country": "91"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"MSG91 Legacy API Response: {response.status_code}, Body: {response.text}")
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('type') == 'success':
                return True
            else:
                logger.error(f"MSG91 Legacy API Error: {response.text}")
                return False
        else:
            logger.error(f"MSG91 Legacy API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"MSG91 Legacy Request Failed: {str(e)}")
        return False


def send_email_otp(email, otp):
    """
    Sends an OTP via Email.
    """
    subject = "Your Verification Code"
    message = f"Your verification code is: {otp}\n\nPlease enter this code to verify your account."
    from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        send_mail(subject, message, from_email, [email])
        return True
    except Exception as e:
        logger.error(f"Email OTP Failed: {str(e)}")
        return False

