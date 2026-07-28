from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import SubscriptionPlan, PlanPricing, UserSubscription
from .forms import SubscriptionPlanForm, PlanPricingFormSet, PlanFeatureFormSet
from django.utils import timezone
from datetime import timedelta
from Apps.Administration.auth_utils import get_user_role
from django.utils import timezone
from datetime import timedelta


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
        form = SubscriptionPlanForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                plan = form.save()
                pricing_formset = PlanPricingFormSet(request.POST, request.FILES, instance=plan)
                feature_formset = PlanFeatureFormSet(request.POST, request.FILES, instance=plan)

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
        form = SubscriptionPlanForm(request.POST, request.FILES, instance=plan)
        pricing_formset = PlanPricingFormSet(request.POST, request.FILES, instance=plan)
        feature_formset = PlanFeatureFormSet(request.POST, request.FILES, instance=plan)

        if form.is_valid() and pricing_formset.is_valid() and feature_formset.is_valid():
            form.save()
            pricing_formset.save()
            feature_formset.save()
            messages.success(request, f"Plan '{plan.name}' updated successfully.")
            return redirect("subscriptions:manage-subscriptions")
        else:
            print("FORM ERRORS:", form.errors)
            print("PRICING ERRORS:", pricing_formset.errors)
            print("PRICING NON FORM:", pricing_formset.non_form_errors())
            print("FEATURE ERRORS:", feature_formset.errors)
            print("FEATURE NON FORM:", feature_formset.non_form_errors())
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

@login_required
def checkout_free_plan(request, plan_id):
    """Instantly activate a free plan (like Seed) for the agent."""
    user_role = get_user_role(request.user) if hasattr(request.user, 'agent_profile') else 'customer'
    if user_role != 'agent':
        messages.error(request, "Only agents can subscribe to these plans.")
        return redirect('public:subscription_plans')

    plan = get_object_or_404(SubscriptionPlan, pk=plan_id)
    
    # Check if there is a 0 price pricing for this plan (e.g. Seed is 0)
    # We'll just grab the 12M pricing or the first available 0 price
    pricing = PlanPricing.objects.filter(plan=plan, price=0).first()
    
    if not pricing:
        # If it's a paid plan, we simulate it for now as per instructions (wait for payment gateway)
        pricing = PlanPricing.objects.filter(plan=plan).first()

    # Create or update UserSubscription
    # We will grant 1 year of access
    end_date = timezone.now() + timedelta(days=365)
    
    UserSubscription.objects.update_or_create(
        user=request.user,
        defaults={
            'plan': plan,
            'pricing': pricing,
            'start_date': timezone.now(),
            'end_date': end_date,
            'status': 'active',
            'auto_renew': False
        }
    )
    
    messages.success(request, f"Congratulations! You have successfully subscribed to the {plan.name} plan.")
    return redirect('agent:property_type_select')


@login_required
def checkout_paid_plan(request, plan_id):
    """Initiates Cashfree checkout session for a paid plan"""
    from django.conf import settings
    from django.urls import reverse
    import uuid
    import time
    from cashfree_pg.models.create_order_request import CreateOrderRequest
    from cashfree_pg.api_client import Cashfree
    from cashfree_pg.models.customer_details import CustomerDetails
    from cashfree_pg.models.order_meta import OrderMeta
    
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    billing_cycle = request.GET.get('billing_cycle', '1M')
    pricing = plan.pricing_options.filter(billing_cycle=billing_cycle).first()
    
    if not pricing:
        messages.error(request, "Invalid billing cycle selected.")
        return redirect('public:subscription_plans')
        
    if pricing.price <= 0:
        return redirect('subscriptions:checkout-free', plan_id=plan.id)
        
    cashfree_env = Cashfree.SANDBOX if settings.CASHFREE_ENVIRONMENT == "SANDBOX" else Cashfree.PRODUCTION
    cashfree = Cashfree(
        XEnvironment=cashfree_env,
        XClientId=settings.CASHFREE_APP_ID,
        XClientSecret=settings.CASHFREE_SECRET_KEY
    )
    
    order_id = f"ORDER_{request.user.id}_{int(time.time())}"
    
    customer_details = CustomerDetails(
        customer_id=f"USER_{request.user.id}",
        customer_phone=getattr(request.user, 'profile_phone', '9999999999'),
        customer_name=request.user.get_full_name() or request.user.username,
        customer_email=request.user.email or "test@example.com"
    )
    
    order_meta = OrderMeta(
        return_url=request.build_absolute_uri(reverse('subscriptions:payment-callback')) + f"?order_id={order_id}",
        notify_url=request.build_absolute_uri(reverse('subscriptions:cashfree-webhook'))
    )
    
    create_order_request = CreateOrderRequest(
        order_id=order_id,
        order_amount=float(pricing.price),
        order_currency="INR",
        customer_details=customer_details,
        order_meta=order_meta
    )
    
    from .models import PaymentTransaction
    # Create the transaction record
    PaymentTransaction.objects.create(
        user=request.user,
        order_id=order_id,
        amount=pricing.price,
        status='PENDING'
    )
    
    try:
        api_response = cashfree.PGCreateOrder(create_order_request=create_order_request)
        payment_session_id = api_response.data.payment_session_id
        
        # Save pending subscription
        UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'pricing': pricing,
                'status': 'pending',
                'stripe_subscription_id': order_id  # Reusing this field for order_id for now
            }
        )
        
        context = {
            'payment_session_id': payment_session_id,
            'plan': plan,
            'pricing': pricing,
            'environment': settings.CASHFREE_ENVIRONMENT
        }
        return render(request, 'public/subscription/checkout.html', context)
        
    except Exception as e:
        messages.error(request, f"Payment gateway initialization failed: {str(e)}")
        return redirect('public:subscription_plans')


def _create_ledger_entries_for_subscription(user, transaction):
    """Helper to create double-entry ledger logs"""
    from .models import LedgerEntry
    
    # Get last balance
    last_entry = LedgerEntry.objects.filter(user=user).order_by('-created_at', '-id').first()
    current_balance = last_entry.balance_after_transaction if last_entry else 0
    
    # 1. Credit Entry (Money In from Payment)
    credit_balance = current_balance + transaction.amount
    LedgerEntry.objects.create(
        user=user,
        payment_transaction=transaction,
        transaction_type='CREDIT',
        amount=transaction.amount,
        balance_after_transaction=credit_balance,
        description=f"Payment received (Order #{transaction.order_id})"
    )
    
    # 2. Debit Entry (Money Out for Subscription)
    debit_balance = credit_balance - transaction.amount
    plan_name = transaction.subscription.plan.name if transaction.subscription and transaction.subscription.plan else "Subscription"
    LedgerEntry.objects.create(
        user=user,
        payment_transaction=transaction,
        transaction_type='DEBIT',
        amount=transaction.amount,
        balance_after_transaction=debit_balance,
        description=f"Subscription Purchase - {plan_name}"
    )

@login_required
def cashfree_callback(request):
    """Handles the redirect from Cashfree after payment attempt"""
    from django.conf import settings
    from cashfree_pg.api_client import Cashfree
    
    order_id = request.GET.get('order_id')
    if not order_id:
        messages.error(request, "Invalid payment response.")
        return redirect('public:subscription_plans')
        
    cashfree_env = Cashfree.SANDBOX if settings.CASHFREE_ENVIRONMENT == "SANDBOX" else Cashfree.PRODUCTION
    cashfree = Cashfree(
        XEnvironment=cashfree_env,
        XClientId=settings.CASHFREE_APP_ID,
        XClientSecret=settings.CASHFREE_SECRET_KEY
    )
    
    try:
        # Fetch the order status
        api_response = cashfree.PGFetchOrder(order_id=order_id)
        
        from .models import PaymentTransaction
        transaction = PaymentTransaction.objects.filter(order_id=order_id).first()
        if transaction:
            transaction.raw_response = str(api_response.data)
            
            # Save the cashfree_payment_id if available (using cf_order_id or fetching payment)
            if hasattr(api_response.data, 'cf_order_id') and api_response.data.cf_order_id:
                transaction.cashfree_payment_id = str(api_response.data.cf_order_id)
                
            transaction.save()
        
        if api_response.data.order_status == "PAID":
            if transaction:
                transaction.status = 'SUCCESS'
                transaction.save()
                
            # Update subscription to active
            user_sub = UserSubscription.objects.filter(user=request.user, stripe_subscription_id=order_id).first()
            if user_sub:
                user_sub.status = 'active'
                user_sub.start_date = timezone.now()
                
                # Calculate end date based on billing cycle
                cycle_mapping = {'1M': 30, '3M': 90, '6M': 180, '12M': 365}
                days = cycle_mapping.get(user_sub.pricing.billing_cycle, 30) if user_sub.pricing else 30
                user_sub.end_date = timezone.now() + timedelta(days=days)
                
                user_sub.save()
                
                if transaction:
                    transaction.subscription = user_sub
                    transaction.save()
                    _create_ledger_entries_for_subscription(request.user, transaction)
                    
                messages.success(request, f"Payment Successful! You are now subscribed to the {user_sub.plan.name} plan.")
                return redirect('agent:property_type_select')
            else:
                messages.error(request, "Subscription record not found.")
                return redirect('public:subscription_plans')
        else:
            if transaction:
                transaction.status = 'FAILED'
                transaction.save()
            messages.error(request, f"Payment failed or pending (Status: {api_response.data.order_status}).")
            return redirect('public:subscription_plans')
            
    except Exception as e:
        messages.error(request, f"Error verifying payment: {str(e)}")
        return redirect('public:subscription_plans')

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

@csrf_exempt
def cashfree_webhook(request):
    """Secure Cashfree Webhook endpoint to capture dropped payments"""
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)
        
    from django.conf import settings
    from cashfree_pg.api_client import Cashfree
    from .models import PaymentTransaction, UserSubscription
    
    cashfree_env = Cashfree.SANDBOX if settings.CASHFREE_ENVIRONMENT == "SANDBOX" else Cashfree.PRODUCTION
    cashfree = Cashfree(
        XEnvironment=cashfree_env,
        XClientId=settings.CASHFREE_APP_ID,
        XClientSecret=settings.CASHFREE_SECRET_KEY
    )
    
    # Verify Signature
    signature = request.headers.get("x-webhook-signature")
    timestamp = request.headers.get("x-webhook-timestamp")
    payload = request.body.decode('utf-8')
    
    if not signature or not timestamp:
        return HttpResponse("Missing headers", status=400)
        
    try:
        cashfree.PGVerifyWebhookSignature(signature, payload, timestamp)
    except Exception as e:
        return HttpResponse("Invalid signature", status=400)
        
    try:
        data = json.loads(payload)
        event_type = data.get('type')
        order_id = data.get('data', {}).get('order', {}).get('order_id')
        cf_payment_id = data.get('data', {}).get('payment', {}).get('cf_payment_id')
        
        if not order_id:
            return HttpResponse("No order_id found", status=400)
            
        transaction = PaymentTransaction.objects.filter(order_id=order_id).first()
        if not transaction:
            return HttpResponse("Transaction not found", status=404)
            
        if cf_payment_id:
            transaction.cashfree_payment_id = str(cf_payment_id)
            transaction.save()
            
        if event_type == "PAYMENT_SUCCESS_WEBHOOK":
            if transaction.status != 'SUCCESS':
                transaction.status = 'SUCCESS'
                # Activate subscription
                user_sub = UserSubscription.objects.filter(stripe_subscription_id=order_id).first()
                if user_sub and user_sub.status != 'active':
                    user_sub.status = 'active'
                    user_sub.start_date = timezone.now()
                    cycle_mapping = {'1M': 30, '3M': 90, '6M': 180, '12M': 365}
                    days = cycle_mapping.get(user_sub.pricing.billing_cycle, 30) if user_sub.pricing else 30
                    user_sub.end_date = timezone.now() + timedelta(days=days)
                    user_sub.save()
                    transaction.subscription = user_sub
                    
                _create_ledger_entries_for_subscription(transaction.user, transaction)
                
        elif event_type == "PAYMENT_FAILED_WEBHOOK":
            transaction.status = 'FAILED'
        elif event_type == "PAYMENT_USER_DROPPED_WEBHOOK":
            transaction.status = 'USER_DROPPED'
            
        transaction.raw_response = payload
        transaction.save()
        
        return HttpResponse("OK")
    except Exception as e:
        return HttpResponse(f"Error processing webhook: {str(e)}", status=500)
