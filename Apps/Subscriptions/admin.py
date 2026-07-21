from django.contrib import admin
from .models import SubscriptionPlan, PlanPricing, PlanFeature, UserSubscription, PaymentTransaction, LedgerEntry

# Register your models here.

class PlanPricingInline(admin.TabularInline):
    model = PlanPricing
    extra = 1
    fields = ("billing_cycle", "price", "original_price", "save_percentage",
              "is_default", "stripe_price_id")


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1
    fields = ("feature_name", "feature_value", "is_available", "display_order")
    readonly_fields = ()
    ordering = ("display_order",)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "badge_text", "is_active", "display_order")
    list_filter = ("is_active",)
    list_editable = ("is_active", "display_order")
    search_fields = ("name", "slug", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order",)
    inlines = [PlanPricingInline, PlanFeatureInline]

    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "slug", "short_description", "badge_text")
        }),
        ("Call To Action", {
            "fields": ("button_text", "button_url")
        }),
        ("Status & Ordering", {
            "fields": ("is_active", "display_order")
        }),
    )


@admin.register(PlanPricing)
class PlanPricingAdmin(admin.ModelAdmin):
    list_display = ("plan", "billing_cycle", "price", "original_price",
                     "save_percentage", "is_default")
    list_filter = ("billing_cycle", "is_default", "plan")
    search_fields = ("plan__name", "stripe_price_id")
    autocomplete_fields = ("plan",)
    list_editable = ("price", "is_default")


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ("plan", "feature_name", "feature_value", "is_available", "display_order")
    list_filter = ("is_available", "plan")
    search_fields = ("feature_name", "plan__name")
    autocomplete_fields = ("plan",)
    list_editable = ("feature_value", "is_available", "display_order")
    ordering = ("plan", "display_order")

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "start_date", "end_date", "auto_renew")
    list_filter = ("status", "auto_renew", "plan")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "stripe_subscription_id")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "start_date"

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("order_id", "user", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("order_id", "cashfree_payment_id", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "raw_response")
    date_hierarchy = "created_at"

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "balance_after_transaction", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("user__username", "user__email", "description")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"