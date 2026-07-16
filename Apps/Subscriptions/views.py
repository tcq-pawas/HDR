from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import SubscriptionPlan
from .forms import SubscriptionPlanForm, PlanPricingFormSet, PlanFeatureFormSet


@login_required
def manage_subscriptions(request):
    """List page - shows all subscription plans in the dashboard table."""
    plans = SubscriptionPlan.objects.all().order_by("display_order")
    context = {
        "plans": plans,
        "page_title": "Manage Subscriptions",
    }
    return render(request, "subscriptions/plan_list.html", context)


@login_required
def add_subscription_plan(request):
    """Add page - create a plan along with its pricing rows and feature rows in one go."""
    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                plan = form.save()
                pricing_formset = PlanPricingFormSet(request.POST, instance=plan)
                feature_formset = PlanFeatureFormSet(request.POST, instance=plan)

                if pricing_formset.is_valid() and feature_formset.is_valid():
                    pricing_formset.save()
                    feature_formset.save()
                    messages.success(request, f"Plan '{plan.name}' created successfully.")
                    return redirect("subscriptions:manage-subscriptions")
                else:
                    transaction.set_rollback(True)
                    messages.error(request, "Please fix the errors in pricing/features below.")
        else:
            pricing_formset = PlanPricingFormSet(request.POST)
            feature_formset = PlanFeatureFormSet(request.POST)
            messages.error(request, "Please fix the errors below.")
    else:
        form = SubscriptionPlanForm()
        pricing_formset = PlanPricingFormSet()
        feature_formset = PlanFeatureFormSet()

    context = {
        "form": form,
        "pricing_formset": pricing_formset,
        "feature_formset": feature_formset,
        "page_title": "Add Subscription Plan",
        "is_edit": False,
    }
    return render(request, "subscriptions/plan_form.html", context)


@login_required
def edit_subscription_plan(request, pk):
    """Edit page - update a plan, its pricing rows and its feature rows together."""
    plan = get_object_or_404(SubscriptionPlan, pk=pk)

    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST, instance=plan)
        pricing_formset = PlanPricingFormSet(request.POST, instance=plan)
        feature_formset = PlanFeatureFormSet(request.POST, instance=plan)

        if form.is_valid() and pricing_formset.is_valid() and feature_formset.is_valid():
            form.save()
            pricing_formset.save()
            feature_formset.save()
            messages.success(request, f"Plan '{plan.name}' updated successfully.")
            return redirect("subscriptions:manage-subscriptions")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SubscriptionPlanForm(instance=plan)
        pricing_formset = PlanPricingFormSet(instance=plan)
        feature_formset = PlanFeatureFormSet(instance=plan)

    context = {
        "form": form,
        "pricing_formset": pricing_formset,
        "feature_formset": feature_formset,
        "plan": plan,
        "page_title": f"Edit Plan - {plan.name}",
        "is_edit": True,
    }
    return render(request, "subscriptions/plan_form.html", context)


@login_required
def delete_subscription_plan(request, pk):
    """Delete a plan (and its pricing/features via CASCADE)."""
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    if request.method == "POST":
        plan_name = plan.name
        plan.delete()
        messages.success(request, f"Plan '{plan_name}' deleted.")
        return redirect("subscriptions:manage-subscriptions")
    context = {"plan": plan, "page_title": "Delete Plan"}
    return render(request, "subscriptions/plan_confirm_delete.html", context)


@login_required
def toggle_plan_status(request, pk):
    """Quick action - flip is_active from the list table without opening the edit page."""
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    plan.is_active = not plan.is_active
    plan.save(update_fields=["is_active"])
    messages.success(request, f"Plan '{plan.name}' is now {'Active' if plan.is_active else 'Inactive'}.")
    return redirect("subscriptions:manage-subscriptions")