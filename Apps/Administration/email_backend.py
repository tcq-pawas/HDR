from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend

class SystemSettingsEmailBackend(EmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        from Apps.Administration.models import SystemSettings
        
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
            self.__class__ = ConsoleBackend
            ConsoleBackend.__init__(self, fail_silently=fail_silently, **kwargs)
