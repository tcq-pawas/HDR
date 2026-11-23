import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from Apps.Administration.services.bulksms import send_sms

logger = logging.getLogger(__name__)

def notify_agent_on_inquiry(property_obj, customer_name, customer_email, customer_phone, customer_message):
    seller = getattr(property_obj, 'seller', None)
    if not seller:
        print(f"[NOTIFICATION] Property {property_obj.id} has no seller assigned.")
        return

    agent_email = seller.email
    agent_phone = getattr(getattr(seller, 'agent_profile', None), 'phone', None)
    agent_name = seller.get_full_name() or seller.username
    property_title = property_obj.title

    print("==================================================")
    print("[AGENT NOTIFICATION TRIGGERED]")
    print(f"Property: {property_title} (ID: {property_obj.id})")
    print(f"Agent: {agent_name} | Email: {agent_email} | Phone: {agent_phone}")
    print(f"Customer: {customer_name} | Phone: {customer_phone} | Email: {customer_email}")
    print(f"Message: {customer_message}")

    # 1. Send Email Notification to Agent
    if agent_email:
        subject = f"New Inquiry Received for {property_title}"

        # Plain text fallback
        plain_message = (
            f"Hello {agent_name},\n\n"
            f"You have received a new inquiry on your property listing: '{property_title}'.\n\n"
            f"Inquiry Details:\n"
            f"- Customer Name: {customer_name or 'N/A'}\n"
            f"- Phone Number: {customer_phone or 'N/A'}\n"
            f"- Email: {customer_email or 'N/A'}\n"
            f"- Message: {customer_message or 'N/A'}\n\n"
            f"Please log in to your dashboard to view and manage this lead.\n\n"
            f"Regards,\nHhectare Team"
        )

        # Render HTML template
        try:
            domain = getattr(settings, 'SITE_DOMAIN', '127.0.0.1:8000')
            protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
            dashboard_url = f"{protocol}://{domain}/dashboard/"

            html_message = render_to_string('emails/inquiry_notification_agent.html', {
                'agent_name': agent_name,
                'property_title': property_title,
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'customer_message': customer_message,
                'dashboard_url': dashboard_url,
            })
        except Exception as e:
            print(f"[HTML TEMPLATE ERROR]: {e}")
            html_message = None

        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hhectare.com')
            send_mail(
                subject,
                plain_message,
                from_email,
                [agent_email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"[EMAIL SENT TO AGENT]: {agent_email}")
        except Exception as e:
            print(f"[EMAIL FAILED]: {e}")
    else:
        print(f"[EMAIL SKIPPED]: Agent {seller.username} has no email.")

    # 2. Send SMS Notification to Agent
    if agent_phone:
        sms_text = (
            f"New property inquiry for '{property_title}' from {customer_name or 'Customer'}. "
            f"Phone: {customer_phone or 'N/A'}. Check your agent dashboard. - Hhectare"
        )
        try:
            result = send_sms(agent_phone, sms_text)
            print(f"[SMS RESULT FOR AGENT {agent_phone}]: {result}")
        except Exception as e:
            print(f"[SMS FAILED]: {e}")
    else:
        print(f"[SMS SKIPPED]: Agent {seller.username} has no phone.")
    print("==================================================")
