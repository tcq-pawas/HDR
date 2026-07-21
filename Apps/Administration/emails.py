"""
Email utility functions for Contact Inquiry API
Uses Django's send_mail function with website-specific SMTP settings
"""

import logging
from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string
from django.conf import settings


logger = logging.getLogger('contact_inquiry_api')


def send_contact_inquiry_email(inquiry, website_config):
    """
    Sends an HTML email notification for a contact inquiry using Django's send_mail
    with website-specific SMTP settings
    
    Args:
        inquiry: The WebsiteInquiry model instance
        website_config: The website configuration dictionary
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from .utils import generate_email_context
    
    try:
        # Get email details from config
        recipient_email = website_config.get('owner_email')
        email_subject = website_config.get('email_subject', 'New Contact Inquiry')
        email_template = website_config.get('email_template')
        smtp_settings = website_config.get('smtp_settings', {})
        
        if not recipient_email:
            logger.error(f"No recipient email configured for website: {inquiry.website}")
            return False, "Recipient email not configured"
        
        if not email_template:
            logger.error(f"No email template configured for website: {inquiry.website}")
            return False, "Email template not configured"
        
        # Generate email context
        context = generate_email_context(inquiry, website_config)
        
        # Render HTML email body
        html_content = render_to_string(email_template, context)
        
        # Get SMTP settings for this website
        smtp_host = smtp_settings.get('host')
        smtp_port = smtp_settings.get('port', 587)
        smtp_username = smtp_settings.get('username')
        smtp_password = smtp_settings.get('password')
        smtp_use_tls = smtp_settings.get('use_tls', True)
        from_email = smtp_settings.get('from_email', settings.DEFAULT_FROM_EMAIL)
        
        # Create email connection with website-specific SMTP settings
        connection = get_connection(
            host=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=smtp_use_tls,
            fail_silently=False
        )
        
        # Send email using Django's send_mail with custom connection
        send_mail(
            subject=email_subject,
            message='',  # Plain text body (empty, using HTML only)
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
            connection=connection
        )
        
        logger.info(
            f"Contact inquiry email sent successfully to {recipient_email} "
            f"for website {inquiry.website} using SMTP: {smtp_host}"
        )
        
        return True, "Email sent successfully"
        
    except Exception as e:
        logger.error(
            f"Failed to send contact inquiry email for website {inquiry.website}: {str(e)}",
            exc_info=True
        )
        return False, str(e)
