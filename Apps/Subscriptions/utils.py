import logging
from dataclasses import dataclass
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from Apps.Subscriptions.models import PlanPricing, UserSubscription

logger = logging.getLogger(__name__)

# Sentinel so callers can pass subscription=None from .first() without re-fetching
SUBSCRIPTION_UNSET = object()


@dataclass(frozen=True)
class PropertyListingCheck:
    """Result of subscription-based property listing eligibility validation."""
    allowed: bool
    message: str = ""
    title: str = ""
    redirect_to_plans: bool = False


def get_user_subscription(user, subscription=SUBSCRIPTION_UNSET):
    """
    Return the user's UserSubscription, or None if missing.

    Pass ``subscription`` to reuse a prefetched / locked instance.
    Explicit ``None`` (e.g. from ``QuerySet.first()``) is respected and
    will not fall back to another lookup.
    """
    if subscription is not SUBSCRIPTION_UNSET:
        return subscription
    try:
        return user.user_subscription
    except (UserSubscription.DoesNotExist, ObjectDoesNotExist, AttributeError):
        return None


def count_agent_listed_properties(user):
    """
    Count properties that count toward an agent's listing limit.
    Matches existing business rules: all properties owned by the seller.
    """
    # Deferred import avoids circular imports at module load time
    from Apps.PublicPage.models import Property

    return Property.objects.filter(seller=user).count()


def check_property_listing_eligibility(user, subscription=SUBSCRIPTION_UNSET):
    """
    Determine whether ``user`` may add another property listing.

    Checks:
    - Active (non-expired) subscription exists
    - Plan is present and eligible for listings
    - Current listing count is under the plan's property_limit
      (property_limit=0 means unlimited)
    """
    subscription = get_user_subscription(user, subscription=subscription)

    if subscription is None:
        return PropertyListingCheck(
            allowed=False,
            redirect_to_plans=True,
            title="Subscription Required",
            message="You must select a subscription plan before adding properties.",
        )

    if not subscription.is_currently_active:
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
    if limit == 0:
        return PropertyListingCheck(allowed=True)

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

    return PropertyListingCheck(allowed=True)


def auto_assign_free_plan(user):
    """
    Automatically assigns the free subscription plan to an agent
    if they don't already have an active subscription.
    """
    try:
        existing = get_user_subscription(user)
        if existing is not None and (
            existing.is_currently_active or existing.status == 'pending'
        ):
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
                    'auto_renew': False,
                },
            )
            return True

        logger.warning(
            "Failed to auto-assign free plan to %s: No 0-price PlanPricing found.",
            user.username,
        )
        return False

    except Exception as e:
        logger.error("Error assigning free plan to %s: %s", user.username, str(e))
        return False
