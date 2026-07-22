"""
Constants for Contact Inquiry API
Central configuration for website-specific settings
"""

WEBSITE_CONFIG = {
    "heyday": {
        "owner_email": "contact@heydayrealty.com",
        "email_subject": "New Property Inquiry",
        "required_fields": [
            "full_name",
            "phone_number",
            "email",
            "subject",
            "preferred_contact_method",
            "property_type",
            "preferred_location",
            "budget_range",
            "area_size",
            "message"
        ],
        "email_template": "emails/heyday_contact.html",
        "company_name": "HeyDay Realty",
        "smtp_settings": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "theheydayrealty@gmail.com",
            "password": "dyteupqhgvpqkxzq",
            "use_tls": True,
            "from_email": "theheydayrealty@gmail.com"
        }
    },
    "thecodiq": {
        "owner_email": "pawas.singh@thecodiq.com",
        "email_subject": "New Website Inquiry",
        "required_fields": [
            "full_name",
            "phone_number",
            "email",
            "message"
        ],
        "email_template": "emails/thecodiq_contact.html",
        "company_name": "TheCodiQ Global",
        "smtp_settings": {
            "host": "smtp.zoho.com",
            "port": 587,
            "username": "pawas.singh@thecodiq.com",
            "password": "rt4QNAC2YUdg",
            "use_tls": True,
            "from_email": "pawas.singh@thecodiq.com"
        }
    }
}

# Contact method choices
CONTACT_METHOD_CHOICES = [
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('whatsapp', 'WhatsApp'),
    ('both', 'Both Email and Phone'),
]

# Property type choices
PROPERTY_TYPE_CHOICES = [
    ('apartment', 'Apartment'),
    ('villa', 'Villa'),
    ('penthouse', 'Penthouse'),
    ('studio', 'Studio'),
    ('commercial', 'Commercial'),
    ('land', 'Land'),
    ('other', 'Other'),
]

# Budget range choices
BUDGET_RANGE_CHOICES = [
    ('under_10m', 'Under 10 Million'),
    ('10m_20m', '10-20 Million'),
    ('20m_50m', '20-50 Million'),
    ('50m_100m', '50-100 Million'),
    ('above_100m', 'Above 100 Million'),
]

# Area size choices
AREA_SIZE_CHOICES = [
    ('under_1000', 'Under 1000 sqft'),
    ('1000_2000', '1000-2000 sqft'),
    ('2000_3000', '2000-3000 sqft'),
    ('3000_5000', '3000-5000 sqft'),
    ('above_5000', 'Above 5000 sqft'),
]

# API Response messages
SUCCESS_MESSAGE = "Your inquiry has been submitted successfully."
VALIDATION_ERROR_MESSAGE = "Validation failed. Please check the errors below."
UNEXPECTED_ERROR_MESSAGE = "Something went wrong. Please try again later."

# Logging configuration
LOGGER_NAME = 'contact_inquiry_api'
