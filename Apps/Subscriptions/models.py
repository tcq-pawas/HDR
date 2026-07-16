from django.db import models
from django.utils.text import slugify


class SubscriptionPlan(models.Model):
    """
    SUBSCRIPTION PLAN
    Master table for each plan (e.g. Seed, Harvest, Legacy)
    """
    name = models.CharField(max_length=100, help_text="Plan Name e.g. Seed")
    slug = models.SlugField(max_length=120, unique=True, blank=True,
                             help_text="Unique Slug e.g. seed (auto-generated if left blank)")
    short_description = models.CharField(max_length=255, blank=True, null=True,
                                          help_text="Subtitle e.g. Forever Free")
    badge_text = models.CharField(max_length=50, blank=True, null=True,
                                   help_text="Badge e.g. Most Popular")
    button_text = models.CharField(max_length=100, default="Choose Plan",
                                    help_text="Button Text e.g. Choose Plan")
    button_url = models.CharField(max_length=255, blank=True, null=True,
                                   help_text="Button Link e.g. /checkout")
    is_active = models.BooleanField(default=True, help_text="Status")
    display_order = models.PositiveIntegerField(default=1, help_text="Ordering on the pricing page")

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PlanPricing(models.Model):
    """
    PLAN PRICING
    Multiple billing-cycle price options for a single plan
    """
    BILLING_CYCLE_CHOICES = [
        ("1M", "Monthly (1 Month)"),
        ("3M", "Quarterly (3 Months)"),
        ("6M", "Half Yearly (6 Months)"),
        ("12M", "Yearly (12 Months)"),
    ]

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name="pricing_options",
        help_text="Related Plan"
    )
    billing_cycle = models.CharField(max_length=3, choices=BILLING_CYCLE_CHOICES,
                                      help_text="1M/3M/6M/12M")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling Price")
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                          help_text="Old Price (for showing strike-through discount)")
    save_percentage = models.PositiveIntegerField(blank=True, null=True, help_text="Discount %")
    is_default = models.BooleanField(default=False, help_text="Default Billing cycle to pre-select")
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True, help_text="Stripe Price ID")

    class Meta:
        verbose_name = "Plan Pricing"
        verbose_name_plural = "Plan Pricing"
        ordering = ["plan", "billing_cycle"]
        unique_together = ("plan", "billing_cycle")

    def __str__(self):
        return f"{self.plan.name} - {self.get_billing_cycle_display()} (₹{self.price})"


class PlanFeature(models.Model):
    """
    PLAN FEATURES (Merged Master + Mapping)
    List of features shown against each plan
    """
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name="features",
        help_text="Plan"
    )
    feature_name = models.CharField(max_length=150, help_text="Feature Name e.g. Active Listings")
    feature_value = models.CharField(max_length=100, blank=True, null=True,
                                      help_text="Displayed Value e.g. 50 / Unlimited / Yes")
    is_available = models.BooleanField(default=True, help_text="Show tick or cross")
    display_order = models.PositiveIntegerField(default=1, help_text="Ordering of feature row")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan Feature"
        verbose_name_plural = "Plan Features"
        ordering = ["plan", "display_order"]

    def __str__(self):
        return f"{self.plan.name} - {self.feature_name}"