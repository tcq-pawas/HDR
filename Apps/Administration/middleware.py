import logging
from django.utils import timezone
from Apps.Administration.models import SystemSettings
from Apps.Administration.auth_utils import get_user_role

logger = logging.getLogger(__name__)

class SessionTimeoutMiddleware:
    """
    Middleware to enforce session timeout based on SystemSettings.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Exempt admins from session timeout
            if get_user_role(request.user) == 'admin':
                return self.get_response(request)
                
            try:
                timeout_setting = SystemSettings.objects.filter(setting_key='SESSION_TIMEOUT').first()
                if timeout_setting and timeout_setting.setting_value:
                    try:
                        timeout_minutes = int(timeout_setting.setting_value)
                        if timeout_minutes > 0:
                            # Setting expiry to timeout_minutes * 60 seconds
                            # This extends the session on every request
                            request.session.set_expiry(timeout_minutes * 60)
                    except ValueError:
                        pass
            except Exception as e:
                logger.error(f"Error in SessionTimeoutMiddleware: {e}")

        response = self.get_response(request)
        return response
