from django.urls import path
from . import views

app_name = 'agent'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Property Management
    path('properties/', views.property_list, name='property_list'),
    path('property/add/', views.property_add, name='property_add'),
    path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('property/<int:pk>/delete/', views.property_delete, name='property_delete'),
    
    # Images
    path('property/<int:pk>/upload-image/', views.upload_property_image, name='upload_image'),
    path('image/<int:image_id>/delete/', views.delete_property_image, name='delete_image'),
    
    # Inquiries
    path('inquiries/', views.property_inquiries, name='inquiries'),
    
    # Leads
    path('leads/', views.leads, name='leads'),
    
    # Site Visits
    path('site-visits/', views.site_visits, name='site_visits'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
]
