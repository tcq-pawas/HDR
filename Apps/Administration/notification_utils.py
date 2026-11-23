import logging
import os
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from Apps.Administration.services.bulksms import send_sms

logger = logging.getLogger(__name__)

def mask_phone(phone):
    """
    Mask phone number: e.g. '9823456781' -> '982******1'
    """
    if not phone:
        return "N/A"
    clean_phone = str(phone).strip()
    if len(clean_phone) <= 4:
        return clean_phone
    # First 3 chars, middle masked with *, last 1 char visible
    prefix = clean_phone[:3]
    suffix = clean_phone[-1]
    masked_count = len(clean_phone) - 4
    return f"{prefix}{'*' * masked_count}{suffix}"

def mask_email(email):
    """
    Mask email address: e.g. 'pawkumarsingh@gmail.com' -> 'paw*************h@gmail.com'
    """
    if not email:
        return "N/A"
    email = str(email).strip()
    if "@" not in email:
        return email
    username, domain = email.split("@", 1)
    if len(username) <= 4:
        masked_user = username[0] + ("*" * (len(username) - 1))
    else:
        # First 3 characters, middle masked with *, last 1 character visible
        prefix = username[:3]
        suffix = username[-1]
        masked_count = len(username) - 4
        return f"{prefix}{'*' * masked_count}{suffix}@{domain}"
    return f"{masked_user}@{domain}"

def notify_agent_on_inquiry(property_obj, customer_name, customer_email, customer_phone, customer_message):
    seller = getattr(property_obj, 'seller', None)
    if not seller:
        print(f"[NOTIFICATION] Property {property_obj.id} has no seller assigned.")
        return

    agent_email = seller.email
    agent_phone = getattr(getattr(seller, 'agent_profile', None), 'phone', None)
    agent_name = seller.get_full_name() or seller.username
    property_title = property_obj.title

    masked_customer_phone = mask_phone(customer_phone)
    masked_customer_email = mask_email(customer_email)

    print("==================================================")
    print("[AGENT NOTIFICATION TRIGGERED]")
    print(f"Property: {property_title} (ID: {property_obj.id})")
    print(f"Agent: {agent_name} | Email: {agent_email} | Phone: {agent_phone}")
    print(f"Customer: {customer_name} | Phone: {masked_customer_phone} | Email: {masked_customer_email}")
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
            f"- Phone Number: {masked_customer_phone}\n"
            f"- Email: {masked_customer_email}\n"
            f"- Message: {customer_message or 'N/A'}\n\n"
            f"Please log in to your dashboard to view and manage this lead.\n\n"
            f"Regards,\nHhectare Team"
        )

        try:
            domain = getattr(settings, 'SITE_DOMAIN', '127.0.0.1:8000')
            protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
            dashboard_url = f"{protocol}://{domain}/dashboard/"

            # Use live domain logo so email clients load it directly without attachments
            logo_url = "https://hhectare.com/static/img/logo.png"

            html_message = render_to_string('emails/inquiry_notification_agent.html', {
                'agent_name': agent_name,
                'property_title': property_title,
                'customer_name': customer_name,
                'customer_email': masked_customer_email,
                'customer_phone': masked_customer_phone,
                'customer_message': customer_message,
                'dashboard_url': dashboard_url,
            })
        except Exception as e:
            print(f"[HTML TEMPLATE ERROR]: {e}")
            html_message = None

        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hhectare.com')
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=from_email,
                to=[agent_email]
            )

            if html_message:
                msg.attach_alternative(html_message, "text/html")
                # Crucial: set mixed_subtype to 'related' so mail clients embed images inline
                # instead of showing them as downloadable file attachments
                msg.mixed_subtype = 'related'

                logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'email_logo.png')
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-ID', '<email_logo>')
                        img.add_header('Content-Disposition', 'inline', filename='email_logo.png')
                        msg.attach(img)

            msg.send(fail_silently=False)
            print(f"[EMAIL SENT TO AGENT]: {agent_email}")
        except Exception as e:
            print(f"[EMAIL FAILED]: {e}")
    else:
        print(f"[EMAIL SKIPPED]: Agent {seller.username} has no email.")

    # 2. Send SMS Notification to Agent
    if agent_phone:
        sms_text = (
            f"New property inquiry for '{property_title}' from {customer_name or 'Customer'}. "
            f"Phone: {masked_customer_phone}. Check your agent dashboard. - Hhectare"
        )
        try:
            result = send_sms(agent_phone, sms_text)
            print(f"[SMS RESULT FOR AGENT {agent_phone}]: {result}")
        except Exception as e:
            print(f"[SMS FAILED]: {e}")
    else:
        print(f"[SMS SKIPPED]: Agent {seller.username} has no phone.")
    print("==================================================")
