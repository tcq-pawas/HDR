from django.urls import path
from . import views

app_name = 'agent'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),
    path('profile/', views.profile, name='profile'),
    
    # Property Management
    path('properties/', views.property_list, name='property_list'),
    path('property/add/', views.property_type_select, name='property_type_select'),
    path('property/add/<str:property_type>/', views.property_add, name='property_add'),
    path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('property/<int:pk>/delete/', views.property_delete, name='property_delete'),
    path('properties/<int:pk>/view/', views.property_view_details, name='property_view'),
    
    # AJAX
    path('ajax/get-cities/', views.get_cities_by_state, name='get_cities'),
    
    # Lead Management
    path('leads/', views.lead_list, name='lead_list'),
    path('lead/add/', views.lead_add, name='lead_add'),
    path('lead/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('lead/<int:pk>/edit/', views.lead_edit, name='lead_edit'),
    path('lead/<int:pk>/followup/add/', views.lead_add_followup, name='lead_add_followup'),
    
    # Site Visit Management
    path('site-visits/', views.site_visit_list, name='site_visit_list'),
    path('site-visit/add/', views.site_visit_add, name='site_visit_add'),
    path('site-visit/<int:pk>/', views.site_visit_detail, name='site_visit_detail'),
    path('site-visit/<int:pk>/edit/', views.site_visit_edit, name='site_visit_edit'),
    
    # Booking & Sales Management
    path('bookings/', views.booking_list, name='booking_list'),
    path('booking/add/', views.booking_add, name='booking_add'),
    path('booking/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('booking/<int:pk>/edit/', views.booking_edit, name='booking_edit'),
    path('booking/<int:booking_pk>/installment/add/', views.installment_add, name='installment_add'),
    path('installment/<int:pk>/edit/', views.installment_edit, name='installment_edit'),
    
    # Commission Management
    path('commissions/', views.commission_list, name='commission_list'),
    path('commission/<int:pk>/', views.commission_detail, name='commission_detail'),
    
    # Document Management
    path('documents/', views.document_list, name='document_list'),
    path('document/add/', views.document_add, name='document_add'),
    path('document/<int:pk>/delete/', views.document_delete, name='document_delete'),
    
    # Communication Center
    path('communications/', views.communication_list, name='communication_list'),
    path('communication/send/', views.communication_send, name='communication_send'),
    path('message-templates/', views.message_template_list, name='message_template_list'),
    path('message-template/add/', views.message_template_add, name='message_template_add'),
    path('message-template/<int:pk>/edit/', views.message_template_edit, name='message_template_edit'),
    
    # Customer Management
    path('customers/', views.customer_list, name='customer_list'),
    path('customer/<str:phone>/', views.customer_detail, name='customer_detail'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/<str:report_type>/', views.export_report, name='export_report'),
]
