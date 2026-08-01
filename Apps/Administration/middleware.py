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

class AgentKYCMiddleware:
    """
    Middleware to enforce KYC Document verification for paid agents
    across all /agent/ routes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path.startswith('/agent/'):
            # Exempt paths that the agent should always be able to access
            exempt_paths = [
                '/agent/document-verification/',
                '/agent/settings/',
                '/agent/profile/',
                '/agent/change-password/',
                '/agent/delete-account/',
                '/agent/subscription/'
            ]
            
            if not any(request.path.startswith(path) for path in exempt_paths):
                from Apps.Administration.auth_utils import get_user_role
                if get_user_role(request.user) == 'agent':
                    from django.urls import reverse
                    from django.shortcuts import redirect
                    from django.contrib import messages
                    from Apps.Subscriptions.models import UserSubscription
                    from Apps.Agent.models import AgentProfile
                    
                    # Ensure profile exists so they can't bypass the check
                    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
                    
                    # 1. Enforce Subscription Plan Selection first
                    user_sub = UserSubscription.objects.filter(user=request.user).first()
                    if not user_sub:
                        messages.info(request, "Please choose a subscription plan to continue.")
                        return redirect(reverse('public:subscription_plans'))
                        
                    # 2. Enforce Document Verification second (ONLY FOR PAID PLANS)
                    is_paid_plan = user_sub.pricing and user_sub.pricing.price > 0
                    if is_paid_plan and agent_profile.verification_status != 'approved':
                        if agent_profile.verification_status == 'rejected':
                            messages.error(request, "Your document verification was rejected. Please re-upload valid documents.")
                        else:
                            messages.warning(request, "Please verify your documents to access this feature.")
                            
                        return redirect(reverse('agent:document_verification'))
                        
        response = self.get_response(request)
        return response
