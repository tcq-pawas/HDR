from django.utils import timezone
from Apps.PublicPage.models import Property
from Apps.Administration.auth_utils import get_user_role


def sidebar_counts(request):
    """Provide sidebar badge counts for agent dashboard navigation."""
    if not request.user.is_authenticated:
        return {}

    try:
        user_role = get_user_role(request.user)
    except Exception:
        return {}

    if user_role not in ['agent', 'owner']:
        return {}

    from .models import Lead, SiteVisit, Booking, Commission, Document, Communication

    today = timezone.now().date()

    try:
        counts = {
            'sidebar_property_count': Property.objects.filter(seller=request.user).count(),
            'sidebar_lead_count': Lead.objects.filter(agent=request.user).count(),
            'sidebar_site_visit_count': SiteVisit.objects.filter(
                agent=request.user,
                scheduled_date__gte=today,
                status__in=['scheduled', 'confirmed']
            ).count(),
            'sidebar_booking_count': Booking.objects.filter(agent=request.user).count(),
            'sidebar_commission_count': Commission.objects.filter(agent=request.user).count(),
            'sidebar_customer_count': Lead.objects.filter(agent=request.user).values('phone').distinct().count(),
            'sidebar_communication_count': Communication.objects.filter(agent=request.user).count(),
        }
    except Exception:
        counts = {}

    return counts
