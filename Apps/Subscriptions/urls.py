from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.manage_subscriptions, name="manage-subscriptions"),
    path("add/", views.add_subscription_plan, name="add-plan"),
    path("<int:pk>/edit/", views.edit_subscription_plan, name="edit-plan"),
    path("<int:pk>/delete/", views.delete_subscription_plan, name="delete-plan"),
    path("<int:pk>/toggle-status/", views.toggle_plan_status, name="toggle-plan-status"),
]