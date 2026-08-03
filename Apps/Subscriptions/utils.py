import logging
from django.utils import timezone
from datetime import timedelta
from Apps.Subscriptions.models import PlanPricing, UserSubscription

logger = logging.getLogger(__name__)

def auto_assign_free_plan(user):
    """
    Automatically assigns the free subscription plan to an agent 
    if they don't already have an active subscription.
    """
    try:
        # Check if user already has any subscription that is active OR pending
        if hasattr(user, 'user_subscription') and user.user_subscription.status in ['active', 'pending']:
            return False
            
        # Find the Free plan (assuming it's a plan with price=0)
        free_pricing = PlanPricing.objects.filter(price=0).first()
        
        if free_pricing:
            end_date = timezone.now() + timedelta(days=365)
            
            UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': free_pricing.plan,
                    'pricing': free_pricing,
                    'start_date': timezone.now(),
                    'end_date': end_date,
                    'status': 'active',
                    'auto_renew': False
                }
            )
            return True
            
        logger.warning(f"Failed to auto-assign free plan to {user.username}: No 0-price PlanPricing found.")
        return False
        
    except Exception as e:
        logger.error(f"Error assigning free plan to {user.username}: {str(e)}")
        return False
