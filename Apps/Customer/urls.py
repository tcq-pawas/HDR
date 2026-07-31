from django.urls import path
from . import views
from .dashboard_views import (
    CustomerDashboardView, CustomerProfileView, CustomerEditProfileView,
    CustomerInquiriesView,
    CustomerSavedPropertiesView, CustomerViewingsView,
    update_profile, change_password, CustomerInquiryDetailView
)

app_name = 'customer'

urlpatterns = [
    # Dashboard
    path('dashboard/', CustomerDashboardView.as_view(), name='dashboard'),
    path('profile/', CustomerProfileView.as_view(), name='profile-page'),
    path('profile/edit/', CustomerEditProfileView.as_view(), name='edit-profile-page'),
    path('inquiries/', CustomerInquiriesView.as_view(), name='inquiries-page'),
    path('saved-properties/', CustomerSavedPropertiesView.as_view(), name='saved-properties-page'),
    path('viewings/', CustomerViewingsView.as_view(), name='viewings-page'),
    path("create-inquiry/", views.create_inquiry, name="create_inquiry"),
    path("api/advisor-properties/<int:agent_profile_id>/", views.get_advisor_properties,name="advisor-properties"),
    path("inquiries/view/<int:pk>/",CustomerInquiryDetailView.as_view(),name="inquiry-detail-page"),
    # Form submission endpoints
    path('update-profile/', update_profile, name='update-profile'),
    path('change-password/', change_password, name='change-password'),

    # API endpoints
    path('api/profile/', views.CustomerProfileView.as_view(), name='profile'),
    path('api/inquiries/', views.InquiryListCreateView.as_view(), name='inquiry-list'),
    path('api/inquiries/<int:pk>/', views.InquiryDetailView.as_view(), name='inquiry-detail'),
    path('api/saved-properties/', views.SavedPropertyListCreateView.as_view(), name='saved-property-list'),
    path('api/saved-properties/<int:pk>/', views.SavedPropertyDetailView.as_view(), name='saved-property-detail'),
    path('api/save-property/<int:property_id>/', views.save_property, name='save-property'),
    path('api/unsave-property/<int:property_id>/', views.unsave_property, name='unsave-property'),
    path('api/viewings/', views.PropertyViewingListCreateView.as_view(), name='viewing-list'),
    path('api/viewings/<int:pk>/', views.PropertyViewingDetailView.as_view(), name='viewing-detail'),
    path('api/feedback/', views.CustomerFeedbackListCreateView.as_view(), name='feedback-list'),
    path('api/feedback/<int:pk>/', views.CustomerFeedbackDetailView.as_view(), name='feedback-detail'),
]
