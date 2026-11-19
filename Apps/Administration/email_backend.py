import logging
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend

logger = logging.getLogger(__name__)


class SystemSettingsEmailBackend(EmailBackend):
    """
    SMTP EmailBackend that loads configuration from the database (SystemSettings),
    falling back to standard Django settings (from .env / settings.py),
    and only falling back to ConsoleBackend in DEBUG mode if no SMTP host/user is configured.
    """
    def __init__(self, fail_silently=False, **kwargs):
        from Apps.Administration.models import SystemSettings

        db_settings = {}
        try:
            for s in SystemSettings.objects.filter(setting_key__startswith='EMAIL_'):
                if s.setting_value:
                    db_settings[s.setting_key] = s.setting_value.strip()
        except Exception as e:
            # Table might not exist yet during initial migrations or DB is unavailable
            logger.debug("Could not read email settings from SystemSettings table: %s", e)
            db_settings = {}

        # 1. Host
        if 'host' not in kwargs:
            kwargs['host'] = (
                db_settings.get('EMAIL_HOST')
                or getattr(settings, 'EMAIL_HOST', None)
            )

        # 2. Port
        if 'port' not in kwargs:
            raw_port = db_settings.get('EMAIL_PORT') or getattr(settings, 'EMAIL_PORT', 587)
            try:
                kwargs['port'] = int(raw_port)
            except (ValueError, TypeError):
                kwargs['port'] = 587

        # 3. Username
        if 'username' not in kwargs:
            kwargs['username'] = (
                db_settings.get('EMAIL_HOST_USER')
                or getattr(settings, 'EMAIL_HOST_USER', None)
            )

        # 4. Password
        if 'password' not in kwargs:
            kwargs['password'] = (
                db_settings.get('EMAIL_HOST_PASSWORD')
                or getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            )

        # 5. TLS / SSL
        if 'use_tls' not in kwargs:
            use_tls_val = db_settings.get('EMAIL_USE_TLS')
            if use_tls_val is not None:
                kwargs['use_tls'] = str(use_tls_val).lower() in ('true', '1', 't', 'y', 'yes')
            else:
                kwargs['use_tls'] = getattr(settings, 'EMAIL_USE_TLS', True)

        if 'use_ssl' not in kwargs:
            use_ssl_val = db_settings.get('EMAIL_USE_SSL')
            if use_ssl_val is not None:
                kwargs['use_ssl'] = str(use_ssl_val).lower() in ('true', '1', 't', 'y', 'yes')
            else:
                kwargs['use_ssl'] = getattr(settings, 'EMAIL_USE_SSL', False)

        kwargs['fail_silently'] = fail_silently

        # If a host is configured, initialize the standard SMTP backend
        if kwargs.get('host'):
            try:
                super().__init__(**kwargs)
                return
            except Exception as e:
                logger.error("Failed to initialize SMTP email backend: %s", e)
                if not fail_silently and not getattr(settings, 'DEBUG', False):
                    raise

        # If no host is configured and running in DEBUG, fall back to console backend
        if getattr(settings, 'DEBUG', False):
            logger.warning(
                "SMTP host is not configured; falling back to ConsoleBackend for local development."
            )
            self.__class__ = ConsoleBackend
            ConsoleBackend.__init__(self, fail_silently=fail_silently, **kwargs)
        else:
            # In production, initialize standard SMTP so configuration errors are visible
            super().__init__(**kwargs)
