from django.contrib import admin
from .models import (
    InvestorProfile, InvestmentListing, Investment, InvestmentRequest, Notification, InvestmentReport, PropertyValuation, ROIHistory, ROIData,
    InvestorDocument, InvestorMeeting
)


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'investor_type', 'company_name', 'phone', 'kyc_status', 'verified', 'created_at']
    list_filter = ['investor_type', 'risk_tolerance', 'kyc_status', 'verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'company_name', 'phone', 'pan_number']
    readonly_fields = ['created_at', 'updated_at', 'kyc_verified_at']


@admin.register(InvestmentListing)
class InvestmentListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'property_obj', 'investment_type', 'total_investment_needed', 
                   'expected_roi_percentage', 'status', 'featured', 'created_at']
    list_filter = ['investment_type', 'status', 'featured', 'created_at']
    search_fields = ['title', 'description', 'property_obj__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'listing', 'amount', 'current_value', 'profit_loss', 'profit_loss_percentage', 'status', 'investment_date']
    list_filter = ['status', 'investment_date', 'confirmed_date', 'last_valuation_date']
    search_fields = ['investor__username', 'listing__title', 'notes']
    readonly_fields = ['investment_date']
    date_hierarchy = 'investment_date'


@admin.register(InvestmentRequest)
class InvestmentRequestAdmin(admin.ModelAdmin):
    list_display = ['investor', 'listing', 'amount', 'status', 'agent_assigned', 'document_verification_status', 'created_at']
    list_filter = ['status', 'document_verification_status', 'created_at', 'approved_at', 'rejected_at']
    search_fields = ['investor__username', 'listing__title', 'admin_notes']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'rejected_at']
    date_hierarchy = 'created_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'


@admin.register(InvestmentReport)
class InvestmentReportAdmin(admin.ModelAdmin):
    list_display = ['investor', 'report_type', 'report_format', 'title', 'generated_at']
    list_filter = ['report_type', 'report_format', 'generated_at']
    search_fields = ['investor__username', 'title']
    readonly_fields = ['generated_at', 'data_snapshot']
    date_hierarchy = 'generated_at'


@admin.register(PropertyValuation)
class PropertyValuationAdmin(admin.ModelAdmin):
    list_display = ['property_obj', 'valuation_date', 'current_value', 'appreciation_rate', 'valuation_method', 'created_at']
    list_filter = ['valuation_method', 'valuation_date', 'created_at']
    search_fields = ['property_obj__title', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'valuation_date'


@admin.register(ROIHistory)
class ROIHistoryAdmin(admin.ModelAdmin):
    list_display = ['investment', 'record_date', 'roi_percentage', 'cumulative_returns', 'monthly_return', 'created_at']
    list_filter = ['record_date', 'created_at']
    search_fields = ['investment__investor__username', 'investment__listing__title', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'record_date'


@admin.register(ROIData)
class ROIDataAdmin(admin.ModelAdmin):
    list_display = ['investment', 'actual_roi_percentage', 'total_returns', 
                   'last_payment_date', 'next_payment_date', 'payment_frequency']
    list_filter = ['payment_frequency', 'last_payment_date', 'next_payment_date']
    search_fields = ['investment__investor__username', 'investment__listing__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'last_payment_date'


@admin.register(InvestorDocument)
class InvestorDocumentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'document_type', 'title', 'uploaded_at', 'verified', 'verified_at']
    list_filter = ['document_type', 'verified', 'uploaded_at', 'verified_at']
    search_fields = ['investor__username', 'title']
    readonly_fields = ['uploaded_at', 'verified_at']
    date_hierarchy = 'uploaded_at'


@admin.register(InvestorMeeting)
class InvestorMeetingAdmin(admin.ModelAdmin):
    list_display = ['investor', 'meeting_type', 'title', 'scheduled_date', 
                   'duration_minutes', 'status', 'created_at']
    list_filter = ['meeting_type', 'status', 'scheduled_date', 'created_at']
    search_fields = ['investor__username', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
