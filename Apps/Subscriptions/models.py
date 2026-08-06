from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User


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
    badge_image = models.ImageField(upload_to='plan_badges/', null=True, blank=True,
                                     help_text="Plan Logo/Badge (e.g. Seed/Harvest icon)")
    button_text = models.CharField(max_length=100, default="Choose Plan",
                                    help_text="Button Text e.g. Choose Plan")
    button_url = models.CharField(max_length=255, blank=True, null=True,
                                   help_text="Button Link e.g. /checkout")
    is_active = models.BooleanField(default=True, help_text="Status")
    display_order = models.PositiveIntegerField(default=1, help_text="Ordering on the pricing page")
    property_limit = models.PositiveIntegerField(
        default=10,
        help_text="Max properties an agent can list on this plan. Use 0 for unlimited.",
    )

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
    Master Feature Table
    """
    name = models.CharField(
        max_length=150,
        unique=True,
        help_text="Feature Name (e.g. Active Listings)"
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan Feature"
        verbose_name_plural = "Plan Features"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class SubscriptionPlanFeature(models.Model):
    """
    Plan ↔ Feature Mapping
    """
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name="features"
    )
    feature = models.ForeignKey(
        PlanFeature,
        on_delete=models.CASCADE,
        related_name="plans"
    )
    feature_value = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Example: 50, Unlimited, Yes"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Show tick or cross"
    )
    display_order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription Plan Feature"
        verbose_name_plural = "Subscription Plan Features"
        unique_together = ("plan", "feature")
        ordering = ["plan", "display_order"]

    def __str__(self):
        return f"{self.plan.name} - {self.feature.name}"



class UserSubscription(models.Model):
    """
    USER SUBSCRIPTION
    Tracks which user is on which plan, expiry dates, and stripe details.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="user_subscription",
        help_text="Subscriber"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscribers",
        help_text="Purchased Plan"
    )
    pricing = models.ForeignKey(
        PlanPricing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Billing Cycle Chosen (optional for free plans)"
    )
    start_date = models.DateTimeField(auto_now_add=True, help_text="Start Date")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Expiry Date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="Subscription Status")
    stripe_subscription_id = models.CharField(max_length=150, blank=True, null=True, help_text="Stripe ID")
    auto_renew = models.BooleanField(default=True, help_text="Auto Renew")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"

    @property
    def is_expired(self):
        """True when status is expired or end_date has passed."""
        if self.status == 'expired':
            return True
        if self.end_date and self.end_date <= timezone.now():
            return True
        return False

    @property
    def is_currently_active(self):
        """True when subscription is active and not past its end date."""
        return self.status == 'active' and not self.is_expired

class PaymentTransaction(models.Model):
    """
    PAYMENT TRANSACTION
    Audit log of individual payment attempts.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('USER_DROPPED', 'User Dropped'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_transactions")
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True)
    order_id = models.CharField(max_length=150, unique=True, help_text="Our local order ID")
    cashfree_payment_id = models.CharField(max_length=150, blank=True, null=True, help_text="Cashfree's payment reference ID")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    raw_response = models.TextField(blank=True, null=True, help_text="Raw JSON response from webhook/API for debugging")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_id} - {self.status} (₹{self.amount})"

class LedgerEntry(models.Model):
    """
    LEDGER ENTRY
    Single-entry accounting log for users tracking credits and debits.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('CREDIT', 'Credit (Money In)'),
        ('DEBIT', 'Debit (Money Out)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ledger_entries")
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount involved")
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2, help_text="Running balance of the user after this entry")
    description = models.CharField(max_length=255, help_text="e.g. Subscription Purchase - Harvest Plan")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"
        ordering = ["-created_at"]
        
    def __str__(self):
        sign = "+" if self.transaction_type == 'CREDIT' else "-"
        return f"{self.user.username} | {self.transaction_type} {sign}₹{self.amount} | Bal: ₹{self.balance_after_transaction}"