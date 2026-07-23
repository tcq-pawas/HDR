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

# API Response messages
SUCCESS_MESSAGE = "Your inquiry has been submitted successfully."
VALIDATION_ERROR_MESSAGE = "Validation failed. Please check the errors below."
UNEXPECTED_ERROR_MESSAGE = "Something went wrong. Please try again later."

# Logging configuration
LOGGER_NAME = 'contact_inquiry_api'
