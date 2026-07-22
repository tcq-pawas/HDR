from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.manage_subscriptions, name="manage-subscriptions"),
    path("add/", views.add_subscription_plan, name="add-plan"),
    path("<int:pk>/edit/", views.edit_subscription_plan, name="edit-plan"),
    path("<int:pk>/delete/", views.delete_subscription_plan, name="delete-plan"),
    path("<int:pk>/toggle-status/", views.toggle_plan_status, name="toggle-plan-status"),
    path("checkout/<int:plan_id>/", views.checkout_free_plan, name="checkout-free"),
    path("checkout/paid/<int:plan_id>/", views.checkout_paid_plan, name="checkout-paid"),
    path("payment/callback/", views.cashfree_callback, name="payment-callback"),
    path("webhook/cashfree/", views.cashfree_webhook, name="cashfree-webhook"),
]