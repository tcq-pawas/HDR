"""
Custom validators for Contact Inquiry API
Handles email, phone number, and website validation
"""

import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from .constants import WEBSITE_CONFIG


class WebsiteValidator:
    """
    Validates that the website field is a configured website
    """
    
    def __call__(self, value):
        if value not in WEBSITE_CONFIG:
            raise ValidationError(
                f"Invalid website '{value}'. Must be one of: {', '.join(WEBSITE_CONFIG.keys())}"
            )


class PhoneNumberValidator:
    """
    Validates phone number format
    Accepts international formats with + prefix and country code
    """
    
    def __call__(self, value):
        # Remove all non-digit characters except + at the start
        cleaned = re.sub(r'[^\d+]', '', value)
        
        # Check if it starts with + followed by digits, or just digits
        if not (cleaned.startswith('+') and cleaned[1:].isdigit() and len(cleaned[1:]) >= 10) and \
           not (cleaned.isdigit() and len(cleaned) >= 10):
            raise ValidationError(
                "Please enter a valid phone number with country code (e.g., +1234567890)"
            )


class EmailValidatorCustom:
    """
    Custom email validator with stricter rules
    """
    
    def __init__(self):
        self.django_validator = EmailValidator()
    
    def __call__(self, value):
        try:
            self.django_validator(value)
        except ValidationError:
            raise ValidationError("Please enter a valid email address")
        
        # Additional checks
        if value.count('@') != 1:
            raise ValidationError("Please enter a valid email address")
        
        local, domain = value.split('@')
        if not local or not domain:
            raise ValidationError("Please enter a valid email address")
        
        if '.' not in domain:
            raise ValidationError("Please enter a valid email address")


def validate_required_fields_for_website(website, data):
    """
    Validates that all required fields for a specific website are present
    
    Args:
        website: The website identifier (e.g., 'heyday', 'thecodiq')
        data: The submitted data dictionary
    
    Returns:
        dict: Dictionary of field errors if any, empty dict otherwise
    """
    errors = {}
    
    if website not in WEBSITE_CONFIG:
        errors['website'] = [f"Invalid website '{website}'"]
        return errors
    
    required_fields = WEBSITE_CONFIG[website]['required_fields']
    
    for field in required_fields:
        if field not in data or not data[field]:
            errors[field] = ["This field is required."]
    
    return errors
