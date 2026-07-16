from django.urls import path
from . import views
from .dashboard_views import (
    AdminDashboardView, UserManagementView, InquiryManagementView,
    InvestmentManagementView, SystemSettingsView, ReportsView, ActivityLogView,
    UserProfileView, PropertyReviewCenterView, PropertyReviewDetailPageView, InquiryDetailPageView,
    InquiryBulkActionView, InquiryExportCSVView, InquiryExportExcelView,  InquiryDeleteView
)
from . import investor_views
from . import communication_views

app_name = 'admin_dash'

urlpatterns = [
    # Dashboard (strict admin-only access)
    path('profile/', views.view_profile, name="view_profile"),
    path('profile/update/', views.update_admin_profile, name="update_profile"),
    path('dashboard/', AdminDashboardView.as_view(), name='dashboard'),
    path('users/', UserManagementView.as_view(), name='user-management-page'),
    path('users/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
    path('inquiries/<int:pk>/delete/', InquiryDeleteView.as_view(), name='inquiry-delete'),
    
    
    # Investors
    path('investors/', investor_views.InvestorListView.as_view(), name='investor-list'),
    path('investors/create/', investor_views.InvestorCreateView.as_view(), name='investor-create'),
    path('investors/<int:pk>/', investor_views.InvestorDetailView.as_view(), name='investor-detail'),
    path('investors/<int:pk>/edit/', investor_views.InvestorUpdateView.as_view(), name='investor-update'),
    path('investors/<int:pk>/delete/', investor_views.InvestorDeleteView.as_view(), name='investor-delete'),
    path('investors/<int:pk>/toggle-status/', investor_views.InvestorToggleStatusView.as_view(), name='investor-toggle-status'),
    
    path('inquiries/', InquiryManagementView.as_view(), name='inquiry-management-page'),
    path('investments/', InvestmentManagementView.as_view(), name='investment-management-page'),
    path('settings/', SystemSettingsView.as_view(), name='system-settings-page'),
    path('reports/', ReportsView.as_view(), name='reports-page'),
    path('activity/', ActivityLogView.as_view(), name='activity-page'),
    path('inquiries/<int:pk>/', InquiryDetailPageView.as_view(), name='inquiry-detail-page'),
    path('inquiries/bulk-action/', InquiryBulkActionView.as_view(), name='inquiry-bulk-action'),
    path('inquiries/export/csv/', InquiryExportCSVView.as_view(), name='inquiry-export-csv'),
    path('inquiries/export/excel/', InquiryExportExcelView.as_view(), name='inquiry-export-excel'),
    # Communication
    path('communications/', communication_views.AdminCommunicationListView.as_view(), name='communication-list'),
    path('communications/send/', communication_views.AdminCommunicationSendView.as_view(), name='communication-send'),
      
    # Property Review System
    path('property-review/', PropertyReviewCenterView.as_view(), name='property-review'),
    path('property-review/<int:property_id>/', PropertyReviewDetailPageView.as_view(), name='property-review-detail'),
    
    # API endpoints (admin-only access)
    path('api/profile/', views.AdminProfileView.as_view(), name='profile'),
    path('api/settings/', views.SystemSettingsListCreateView.as_view(), name='settings-list'),
    path('api/settings/<int:pk>/', views.SystemSettingsDetailView.as_view(), name='settings-detail'),
    path('api/widgets/', views.DashboardWidgetListCreateView.as_view(), name='widget-list'),
    path('api/widgets/<int:pk>/', views.DashboardWidgetDetailView.as_view(), name='widget-detail'),
    path('api/permissions/', views.UserPermissionListCreateView.as_view(), name='permission-list'),
    path('api/permissions/<int:pk>/', views.UserPermissionDetailView.as_view(), name='permission-detail'),
    path('api/activity/', views.ActivityLogListView.as_view(), name='activity-list'),
    path('api/backups/', views.SystemBackupListCreateView.as_view(), name='backup-list'),
    path('api/backups/<int:pk>/', views.SystemBackupDetailView.as_view(), name='backup-detail'),
    path('api/maintenance/', views.SystemMaintenanceListCreateView.as_view(), name='maintenance-list'),
    path('api/maintenance/<int:pk>/', views.SystemMaintenanceDetailView.as_view(), name='maintenance-detail'),
    path('api/reports/', views.ReportListCreateView.as_view(), name='report-list'),
    path('api/reports/<int:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('api/generated-reports/', views.GeneratedReportListView.as_view(), name='generated-report-list'),
    path('api/notifications/', views.NotificationListCreateView.as_view(), name='notification-list'),
    path('api/notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('api/metrics/', views.SystemMetricsListCreateView.as_view(), name='metrics-list'),
    path('api/users/', views.user_management, name='user-management'),
    path('api/users/<int:user_id>/edit/', views.edit_user, name='user-edit'),
    path('api/users/<int:user_id>/suspend/', views.suspend_user, name='user-suspend'),
    path('api/users/<int:user_id>/activate/', views.activate_user, name='user-activate'),
    path('api/users/<int:user_id>/reset-password/', views.reset_password, name='user-reset-password'),
    path('api/users/<int:user_id>/change-role/', views.change_role, name='user-change-role'),
    path('api/users/<int:user_id>/delete/', views.delete_user, name='user-delete'),
    path('api/log-activity/', views.log_activity, name='log-activity'),
    path('api/dashboard/', views.admin_dashboard, name='dashboard-data'),
    
    # Property Review API endpoints
    path('api/properties/', views.PropertyReviewListView.as_view(), name='property-review-list'),
    path('api/properties/<int:pk>/', views.PropertyReviewDetailView.as_view(), name='property-review-detail-api'),
    path('api/properties/<int:property_id>/approve/', views.approve_property, name='property-approve'),
    path('api/properties/<int:property_id>/reject/', views.reject_property, name='property-reject'),
    path('api/properties/stats/', views.property_review_stats, name='property-review-stats'),
    path('api/settings/save-email/', views.save_email_settings, name='save-email-settings'),
    path('api/settings/test-email/', views.test_email_settings, name='test-email-settings'),
    path('api/settings/save-security/', views.save_security_settings, name='save-security-settings'),
    path('api/settings/save-general/', views.save_general_settings, name='save-general-settings'),
    path('api/inquiries/unread-count/', views.get_unread_inquiries, name='unread-inquiries-count'),
    path('api/investments/create/', views.create_investment, name='create-investment'),
]
