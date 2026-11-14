from django.utils import timezone

def admin_notifications_processor(request):
    """
    Context processor to provide admin header notification counts and recent alerts
    """
    if not request.user.is_authenticated:
        return {}

    is_admin = False
    try:
        from Apps.Administration.auth_utils import get_user_role
        is_admin = (get_user_role(request.user) == 'admin')
    except Exception:
        is_admin = (request.user.is_superuser or request.user.is_staff)

    if not is_admin:
        return {}

    pending_kyc_count = 0
    pending_property_count = 0
    recent_notifications = []

    # 1. Pending KYC Verification Documents
    try:
        from Apps.Agent.models import VerificationDocument
        pending_kyc_count = VerificationDocument.objects.filter(
            is_current=True,
            status__in=['pending_review', 'under_review']
        ).count()
    except Exception:
        pass

    # 2. Pending Property Reviews
    try:
        from Apps.Properties.models import Property
        pending_property_count = Property.objects.filter(
            approval_status='pending'
        ).count()
    except Exception:
        pass

    # 3. Recent Notifications
    try:
        from Apps.Administration.models import Notification
        recent_notifications = list(Notification.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5])
    except Exception:
        pass

    total_notifications = pending_kyc_count + pending_property_count

    return {
        'admin_pending_kyc_count': pending_kyc_count,
        'admin_pending_property_count': pending_property_count,
        'admin_total_notifications_count': total_notifications,
        'admin_recent_notifications': recent_notifications,
    }


def agent_notifications_processor(request):
    """
    Context processor to provide agent header notification counts and recent alerts
    """
    if not request.user.is_authenticated:
        return {}

    is_agent = False
    try:
        from Apps.Administration.auth_utils import get_user_role
        role = get_user_role(request.user)
        is_agent = (role in ['agent', 'owner'])
    except Exception:
        is_agent = hasattr(request.user, 'agent_profile')

    if not is_agent:
        return {}

    new_leads_count = 0
    pending_props_count = 0
    upcoming_visits_count = 0
    recent_agent_notifications = []

    # 1. New leads count
    try:
        from Apps.Agent.models import Lead
        new_leads_count = Lead.objects.filter(agent=request.user, status='new').count()
    except Exception:
        pass

    # 2. Properties pending approval
    try:
        from Apps.Properties.models import Property
        pending_props_count = Property.objects.filter(seller=request.user, status='pending').count()
    except Exception:
        pass

    # 3. Upcoming site visits
    try:
        from Apps.Agent.models import SiteVisit
        upcoming_visits_count = SiteVisit.objects.filter(
            agent=request.user,
            status__in=['scheduled', 'confirmed'],
            scheduled_date__gte=timezone.now().date()
        ).count()
    except Exception:
        pass

    # 4. System notifications targeted to this user or global
    try:
        from Apps.Administration.models import Notification
        from django.db.models import Q
        recent_agent_notifications = list(Notification.objects.filter(
            Q(target_users=request.user) | Q(is_global=True),
            is_active=True
        ).order_by('-created_at')[:5])
    except Exception:
        pass

    agent_total_notifications_count = new_leads_count + pending_props_count + upcoming_visits_count

    return {
        'agent_new_leads_count': new_leads_count,
        'agent_pending_props_count': pending_props_count,
        'agent_upcoming_visits_count': upcoming_visits_count,
        'agent_total_notifications_count': agent_total_notifications_count,
        'agent_recent_notifications': recent_agent_notifications,
    }

