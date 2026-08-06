import logging
from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from Apps.Subscriptions.models import PlanPricing, UserSubscription

logger = logging.getLogger(__name__)

# Seed plan: one listing every N days (existing business rule)
SEED_PLAN_COOLDOWN_DAYS = 4


@dataclass(frozen=True)
class PropertyListingCheck:
    """Result of subscription-based property listing eligibility validation."""
    allowed: bool
    message: str = ""
    title: str = ""
    redirect_to_plans: bool = False


def get_user_subscription(user, subscription=None):
    """
    Return the user's UserSubscription, or None if missing.
    Pass ``subscription`` to reuse a prefetched / locked instance.
    """
    if subscription is not None:
        return subscription
    try:
        return user.user_subscription
    except UserSubscription.DoesNotExist:
        return None


def count_agent_listed_properties(user):
    """
    Count properties that count toward an agent's listing limit.
    Matches existing business rules: all properties owned by the seller.
    """
    # Deferred import avoids circular imports at module load time
    from Apps.PublicPage.models import Property

    return Property.objects.filter(seller=user).count()


def check_property_listing_eligibility(user, subscription=None):
    """
    Determine whether ``user`` may add another property listing.

    Checks:
    - Active (non-expired) subscription exists
    - Plan is present and eligible for listings
    - Current listing count is under the plan's property_limit
      (property_limit=0 means unlimited)
    - Seed-plan cooldown between listings (when applicable)
    """
    subscription = get_user_subscription(user, subscription=subscription)

    if subscription is None:
        return PropertyListingCheck(
            allowed=False,
            redirect_to_plans=True,
            title="Subscription Required",
            message="You must select a subscription plan before adding properties.",
        )

    if subscription.is_expired or subscription.status != 'active':
        if subscription.is_expired:
            return PropertyListingCheck(
                allowed=False,
                redirect_to_plans=True,
                title="Subscription Expired",
                message=(
                    "Your subscription has expired. Please renew or upgrade your plan "
                    "to continue listing properties."
                ),
            )
        return PropertyListingCheck(
            allowed=False,
            redirect_to_plans=True,
            title="Subscription Inactive",
            message=(
                "You don't have an active subscription. Please choose a plan "
                "to list properties."
            ),
        )

    plan = subscription.plan
    if plan is None or not plan.is_active:
        return PropertyListingCheck(
            allowed=False,
            redirect_to_plans=True,
            title="Subscription Required",
            message=(
                "Your current subscription plan is unavailable. "
                "Please choose an active plan before adding properties."
            ),
        )

    limit = plan.property_limit
    # 0 = unlimited listings for this plan
    if limit > 0:
        current_count = count_agent_listed_properties(user)
        if current_count >= limit:
            unit = "property" if limit == 1 else "properties"
            return PropertyListingCheck(
                allowed=False,
                title="Plan Limit Reached",
                message=(
                    f"You have reached your plan's listing limit of {limit} {unit}. "
                    "Please upgrade your subscription or remove an existing property "
                    "before adding another one."
                ),
            )

    if plan.slug and 'seed' in plan.slug.lower():
        from Apps.PublicPage.models import Property

        last_property = (
            Property.objects.filter(seller=user)
            .only('created_at')
            .order_by('-created_at')
            .first()
        )
        if last_property:
            days_passed = (timezone.now() - last_property.created_at).days
            if days_passed < SEED_PLAN_COOLDOWN_DAYS:
                days_left = SEED_PLAN_COOLDOWN_DAYS - days_passed
                return PropertyListingCheck(
                    allowed=False,
                    title="Seed Plan Cooldown",
                    message=(
                        f"Now your today limit is reached, you can add another property "
                        f"after {days_left} days (Seed Plan Limit)."
                    ),
                )

    return PropertyListingCheck(allowed=True)


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
