from django.contrib import admin
from .models import (
    InvestorProfile, InvestmentListing, Investment, ROIData,
    InvestorDocument, InvestorMeeting
)


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'investor_type', 'company_name', 'phone', 'verified', 'created_at']
    list_filter = ['investor_type', 'risk_tolerance', 'verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'company_name', 'phone']
    readonly_fields = ['created_at', 'updated_at']


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
    list_display = ['investor', 'listing', 'amount', 'status', 'investment_date', 'confirmed_date']
    list_filter = ['status', 'investment_date', 'confirmed_date']
    search_fields = ['investor__username', 'listing__title', 'notes']
    readonly_fields = ['investment_date']
    date_hierarchy = 'investment_date'


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
