from django.urls import path
from . import views
from .dashboard_views import (
    InvestorDashboardView, InvestorProfileView, InvestorInvestmentsView,
    InvestorListingsView, InvestorROIDataView, InvestorDocumentsView
)

app_name = 'investor'

urlpatterns = [
    # Dashboard
    path('dashboard/', InvestorDashboardView.as_view(), name='dashboard'),
    path('profile/', InvestorProfileView.as_view(), name='profile-page'),
    path('investments/', InvestorInvestmentsView.as_view(), name='investments-page'),
    path('listings/', InvestorListingsView.as_view(), name='listings-page'),
    path('roi-data/', InvestorROIDataView.as_view(), name='roi-data-page'),
    path('documents/', InvestorDocumentsView.as_view(), name='documents-page'),
    
    # API endpoints
    path('api/profile/', views.InvestorProfileView.as_view(), name='profile'),
    path('api/listings/', views.InvestmentListingListView.as_view(), name='listing-list'),
    path('api/listings/<int:pk>/', views.InvestmentListingDetailView.as_view(), name='listing-detail'),
    path('api/featured/', views.featured_investments, name='featured-listings'),
    path('api/investments/', views.InvestmentListCreateView.as_view(), name='investment-list'),
    path('api/investments/<int:pk>/', views.InvestmentDetailView.as_view(), name='investment-detail'),
    path('api/investments/<int:investment_id>/update-status/', views.update_investment_status, name='update-investment-status'),
    path('api/roi-data/', views.ROIDataListView.as_view(), name='roi-data-list'),
    path('api/roi-data/<int:pk>/', views.ROIDataDetailView.as_view(), name='roi-data-detail'),
    path('api/documents/', views.InvestorDocumentListCreateView.as_view(), name='document-list'),
    path('api/documents/<int:pk>/', views.InvestorDocumentDetailView.as_view(), name='document-detail'),
    path('api/meetings/', views.InvestorMeetingListCreateView.as_view(), name='meeting-list'),
    path('api/meetings/<int:pk>/', views.InvestorMeetingDetailView.as_view(), name='meeting-detail'),
    path('api/dashboard/', views.investment_dashboard, name='dashboard-data'),
]
