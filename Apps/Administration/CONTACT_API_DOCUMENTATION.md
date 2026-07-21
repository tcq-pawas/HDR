# Contact Inquiry API Documentation

## Overview

This is a production-ready, secure, scalable, and reusable Contact Inquiry API built with Django REST Framework. The API handles contact form submissions from multiple websites with dynamic validation based on website configuration.

## Architecture

The API follows Clean Architecture, SOLID Principles, and Django Best Practices:

- **Dynamic Configuration**: Website-specific settings are centralized in `constants.py`
- **Separation of Concerns**: Each component has a single responsibility
- **Extensibility**: Adding new websites requires only configuration changes
- **Error Handling**: Email failures don't fail the API; inquiries are still saved
- **Security**: Input sanitization, validation, and proper error handling

## API Endpoint

```
POST /admin-dashboard/api/contact/
```

## Request Format

### HeyDay Realty

```json
{
    "website": "heyday",
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "email": "john@example.com",
    "subject": "Property Inquiry",
    "preferred_contact_method": "email",
    "property_type": "apartment",
    "preferred_location": "Downtown",
    "budget_range": "10m_20m",
    "area_size": "1000_2000",
    "message": "I am interested in this property."
}
```

### TheCodiQ Global

```json
{
    "website": "thecodiq",
    "full_name": "Jane Smith",
    "phone_number": "+9876543210",
    "email": "jane@example.com",
    "message": "I would like to discuss a project."
}
```

## Response Format

### Success Response (200 OK)

```json
{
    "success": true,
    "message": "Your inquiry has been submitted successfully."
}
```

### Validation Error (400 Bad Request)

```json
{
    "success": false,
    "message": "Validation failed. Please check the errors below.",
    "errors": {
        "phone_number": ["This field is required."],
        "email": ["Please enter a valid email address"]
    }
}
```

### Unexpected Error (500 Internal Server Error)

```json
{
    "success": false,
    "message": "Something went wrong. Please try again later."
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| website | string | Yes | Website identifier ('heyday' or 'thecodiq') |
| full_name | string | Yes | Full name of the contact person |
| phone_number | string | Yes | Phone number with country code |
| email | string | Yes | Valid email address |
| subject | string | HeyDay only | Subject of the inquiry |
| preferred_contact_method | string | HeyDay only | 'email', 'phone', 'whatsapp', or 'both' |
| property_type | string | HeyDay only | 'apartment', 'villa', 'penthouse', etc. |
| preferred_location | string | HeyDay only | Preferred property location |
| budget_range | string | HeyDay only | Budget range category |
| area_size | string | HeyDay only | Area size category |
| message | string | Yes | Inquiry message |

## Adding a New Website

To add support for a new website, follow these steps:

### 1. Add Configuration to `constants.py`

```python
WEBSITE_CONFIG = {
    # ... existing configurations ...
    "newwebsite": {
        "owner_email": "contact@newwebsite.com",
        "email_subject": "New Website Inquiry",
        "required_fields": [
            "full_name",
            "phone_number",
            "email",
            "message"
        ],
        "email_template": "emails/newwebsite_contact.html",
        "company_name": "New Website"
    }
}
```

### 2. Create Email Template

Create `templates/emails/newwebsite_contact.html` with your custom design.

### 3. That's It!

No changes needed to views, serializers, or validators. The API will automatically handle the new website.

## Postman Collection

### Import the following collection into Postman:

```json
{
    "info": {
        "name": "Contact Inquiry API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "HeyDay Realty Contact",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"website\": \"heyday\",\n    \"full_name\": \"John Doe\",\n    \"phone_number\": \"+1234567890\",\n    \"email\": \"john@example.com\",\n    \"subject\": \"Property Inquiry\",\n    \"preferred_contact_method\": \"email\",\n    \"property_type\": \"apartment\",\n    \"preferred_location\": \"Downtown\",\n    \"budget_range\": \"10m_20m\",\n    \"area_size\": \"1000_2000\",\n    \"message\": \"I am interested in this property.\"\n}"
                },
                "url": {
                    "raw": "{{base_url}}/admin-dashboard/api/contact/",
                    "host": ["{{base_url}}"],
                    "path": ["admin-dashboard", "api", "contact", ""]
                }
            }
        },
        {
            "name": "TheCodiQ Global Contact",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"website\": \"thecodiq\",\n    \"full_name\": \"Jane Smith\",\n    \"phone_number\": \"+9876543210\",\n    \"email\": \"jane@example.com\",\n    \"message\": \"I would like to discuss a project.\"\n}"
                },
                "url": {
                    "raw": "{{base_url}}/admin-dashboard/api/contact/",
                    "host": ["{{base_url}}"],
                    "path": ["admin-dashboard", "api", "contact", ""]
                }
            }
        }
    ],
    "variable": [
        {
            "key": "base_url",
            "value": "http://localhost:8000"
        }
    ]
}
```

## File Structure

```
Apps/Administration/
├── constants.py                    # Website configurations
├── validators.py                   # Custom validators
├── utils.py                        # Utility functions
├── emails.py                       # Email service
├── contact_serializers.py          # API serializers
├── contact_views.py                # API views
├── models.py                       # WebsiteInquiry model
├── admin.py                        # Admin configuration
├── urls.py                         # URL configuration
└── templates/
    └── emails/
        ├── heyday_contact.html     # HeyDay email template
        └── thecodiq_contact.html   # TheCodiQ email template
```

## Security Features

- **Input Validation**: All inputs are validated using DRF validators
- **XSS Prevention**: Text inputs are sanitized using HTML escaping
- **SQL Injection Protection**: Django ORM prevents SQL injection
- **Email Validation**: Custom email validator with strict rules
- **Phone Validation**: International phone number format validation
- **Website Validation**: Only configured websites are accepted

## Logging

The API implements comprehensive logging for:

- Validation failures
- Database operations
- Email sending attempts and failures
- Unexpected exceptions

Logs are written to the `contact_inquiry_api` logger.

## Error Handling

- **Email Failures**: Don't fail the API; inquiries are still saved and logged
- **Validation Errors**: Return detailed error messages to the client
- **Unexpected Errors**: Return generic error message to avoid exposing internals
- **Database Errors**: Logged and handled gracefully

## Admin Interface

The `WebsiteInquiry` model is registered in Django Admin with:

- List view with filters for website, contact status, and date
- Search functionality
- Bulk actions for marking inquiries as contacted/uncontacted
- Organized fieldsets for easy data entry
- Read-only metadata fields

## Testing Recommendations

Test the following scenarios:

1. Valid submissions for each website
2. Missing required fields
3. Invalid email formats
4. Invalid phone number formats
5. Invalid website identifiers
6. Email sending failures
7. Database connection failures
8. XSS attempts in text fields
9. Concurrent submissions

## Production Checklist

Before deploying to production:

- [ ] Configure email backend in Django settings
- [ ] Set up proper logging configuration
- [ ] Configure CORS if needed
- [ ] Set up rate limiting
- [ ] Configure CSRF protection
- [ ] Set up monitoring and alerts
- [ ] Configure backup strategy
- [ ] Review and update email templates with production URLs
- [ ] Test email delivery with production email server
- [ ] Configure SSL/HTTPS
- [ ] Set up database backups
