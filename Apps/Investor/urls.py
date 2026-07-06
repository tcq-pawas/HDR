from django.urls import path
from . import views
from .dashboard_views import (
    InvestorDashboardView, InvestorProfileView, InvestorInvestmentsView,
    InvestorROIDataView, InvestorDocumentsView,
    InvestmentDetailView, InvestmentROIView
)

app_name = 'investor'

urlpatterns = [
    # Dashboard
    path('dashboard/', InvestorDashboardView.as_view(), name='dashboard'),
    path('profile/', InvestorProfileView.as_view(), name='profile-page'),
    path('investments/', InvestorInvestmentsView.as_view(), name='investments-page'),
    path('investments/<int:investment_id>/', InvestmentDetailView.as_view(), name='investment-detail'),
    path('investments/<int:investment_id>/roi/', InvestmentROIView.as_view(), name='investment-roi'),
    path('roi-data/', InvestorROIDataView.as_view(), name='roi-data-page'),
    path('documents/', InvestorDocumentsView.as_view(), name='documents-page'),
    
    # API endpoints
    path('api/profile/', views.InvestorProfileView.as_view(), name='profile'),
    path('api/listings/', views.InvestmentListingListView.as_view(), name='listing-list'),
    path('api/listings/<int:pk>/', views.InvestmentListingDetailView.as_view(), name='listing-detail'),
    path('api/featured/', views.featured_investments, name='featured-listings'),
    path('api/investments/', views.InvestmentListCreateView.as_view(), name='investment-list'),
    path('api/investments/<int:pk>/', views.InvestmentDetailView.as_view(), name='api-investment-detail'),
    path('api/investments/<int:investment_id>/update-status/', views.update_investment_status, name='update-investment-status'),
    path('api/investment-requests/', views.InvestmentRequestListCreateView.as_view(), name='investment-request-list'),
    path('api/investment-requests/<int:pk>/', views.InvestmentRequestDetailView.as_view(), name='investment-request-detail'),
    path('api/notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('api/notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('api/notifications/count/', views.notification_count, name='notification-count'),
    path('api/reports/', views.InvestmentReportListCreateView.as_view(), name='report-list'),
    path('api/reports/<int:pk>/', views.InvestmentReportDetailView.as_view(), name='report-detail'),
    path('api/valuations/', views.PropertyValuationListCreateView.as_view(), name='valuation-list'),
    path('api/valuations/<int:pk>/', views.PropertyValuationDetailView.as_view(), name='valuation-detail'),
    path('api/roi-history/', views.ROIHistoryListCreateView.as_view(), name='roi-history-list'),
    path('api/roi-history/<int:pk>/', views.ROIHistoryDetailView.as_view(), name='roi-history-detail'),
    path('api/roi-data/', views.ROIDataListView.as_view(), name='roi-data-list'),
    path('api/roi-data/<int:pk>/', views.ROIDataDetailView.as_view(), name='roi-data-detail'),
    path('api/documents/', views.InvestorDocumentListCreateView.as_view(), name='document-list'),
    path('api/documents/<int:pk>/', views.InvestorDocumentDetailView.as_view(), name='document-detail'),
    path('api/meetings/', views.InvestorMeetingListCreateView.as_view(), name='meeting-list'),
    path('api/meetings/<int:pk>/', views.InvestorMeetingDetailView.as_view(), name='meeting-detail'),
    path('api/dashboard/', views.investment_dashboard, name='dashboard-data'),
]
