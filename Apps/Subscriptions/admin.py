from django.contrib import admin
from .models import SubscriptionPlan, PlanPricing, PlanFeature

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