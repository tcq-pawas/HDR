import os
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend


def attach_hhectare_logo_if_needed(msg):
    """Automatically attaches the official HHectare email logo as an inline CID image if referenced."""
    try:
        has_cid = False
        if hasattr(msg, 'alternatives'):
            for content, mimetype in msg.alternatives:
                if mimetype == 'text/html' and 'cid:hhectare_email_logo' in content:
                    has_cid = True
                    break
        if not has_cid and hasattr(msg, 'body') and isinstance(msg.body, str) and 'cid:hhectare_email_logo' in msg.body:
            has_cid = True

        if not has_cid:
            return

        # Check if already attached
        for att in getattr(msg, 'attachments', []):
            if hasattr(att, 'get') and att.get('Content-ID') == '<hhectare_email_logo>':
                return
            if hasattr(att, 'headers') and any('Content-ID' in str(k) and '<hhectare_email_logo>' in str(v) for k, v in att.headers):
                return

        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'hhectare_email_logo.png')
        if not os.path.exists(logo_path):
            logo_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'img', 'hhectare_email_logo.png')

        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                img = MIMEImage(f.read(), _subtype='png')
                img.add_header('Content-ID', '<hhectare_email_logo>')
                img.add_header('Content-Disposition', 'inline', filename='hhectare-email-logo.png')
                msg.attach(img)
    except Exception:
        pass


class SystemSettingsEmailBackend(EmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        from Apps.Administration.models import SystemSettings
        self._fallback = False
        try:
            kwargs['host'] = SystemSettings.objects.get(setting_key='EMAIL_HOST').setting_value
            kwargs['port'] = int(SystemSettings.objects.get(setting_key='EMAIL_PORT').setting_value)
            kwargs['username'] = SystemSettings.objects.get(setting_key='EMAIL_HOST_USER').setting_value
            kwargs['password'] = SystemSettings.objects.get(setting_key='EMAIL_HOST_PASSWORD').setting_value
            
            use_tls_val = SystemSettings.objects.get(setting_key='EMAIL_USE_TLS').setting_value
            kwargs['use_tls'] = use_tls_val.lower() in ('true', '1', 't', 'y', 'yes')
            kwargs['fail_silently'] = fail_silently
            
            super().__init__(**kwargs)
        except (SystemSettings.DoesNotExist, ValueError, TypeError):
            # Fall back to console backend if not fully configured in the DB
            self._fallback = True
            self._console_backend = ConsoleBackend(fail_silently=fail_silently, **kwargs)

    def send_messages(self, email_messages):
        for msg in email_messages:
            attach_hhectare_logo_if_needed(msg)
        if getattr(self, '_fallback', False):
            return self._console_backend.send_messages(email_messages)
        return super().send_messages(email_messages)
