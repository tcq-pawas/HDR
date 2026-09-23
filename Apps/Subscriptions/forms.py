from django import forms
from django.forms import inlineformset_factory
from .models import SubscriptionPlan, PlanPricing, PlanFeature, SubscriptionPlanFeature


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "name", "slug", "short_description", "badge_text", "badge_image",
            "button_text", "button_url", "is_active", "display_order", "property_limit",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Harvest"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "auto-generated if left blank"}),
            "short_description": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Forever Free"}),
            "badge_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Most Popular"}),
            "badge_image": forms.FileInput(attrs={"class": "form-control"}),
            "button_text": forms.TextInput(attrs={"class": "form-control"}),
            "button_url": forms.TextInput(attrs={"class": "form-control", "placeholder": "/checkout"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "display_order": forms.NumberInput(attrs={"class": "form-control"}),
            "property_limit": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if slug:
            qs = SubscriptionPlan.objects.filter(slug=slug)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This slug is already in use. Please choose another.")
        return slug


class PlanPricingForm(forms.ModelForm):
    class Meta:
        model = PlanPricing
        fields = ["billing_cycle", "price", "original_price", "save_percentage",
                   "is_default", "cashfree_plan_id"]
        widgets = {
            "billing_cycle": forms.Select(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "original_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "save_percentage": forms.NumberInput(attrs={"class": "form-control"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cashfree_plan_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. HARVEST_1M"}),
        }


class MasterPlanFeatureForm(forms.ModelForm):
    """Form for adding/editing Master Features in the Master Table"""
    class Meta:
        model = PlanFeature
        fields = ["name", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Active Listings"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            # "display_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class SubscriptionPlanFeatureForm(forms.ModelForm):
    """Form for mapping plan to feature with value and availability"""
    class Meta:
        model = SubscriptionPlanFeature
        fields = ["feature", "feature_value", "is_available"]
        widgets = {
            "feature": forms.Select(attrs={"class": "form-control"}),
            "feature_value": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 50 / Unlimited / Yes"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            # "display_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


# Formsets
PlanPricingFormSet = inlineformset_factory(
    SubscriptionPlan, PlanPricing,
    form=PlanPricingForm,
    extra=0,
    can_delete=True,
)

SubscriptionPlanFeatureFormSet = inlineformset_factory(
    SubscriptionPlan, SubscriptionPlanFeature,
    form=SubscriptionPlanFeatureForm,
    extra=0,
    can_delete=False,
)
