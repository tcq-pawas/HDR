from django.contrib import admin
from .models import (
    AgentProfile, Lead, LeadFollowUp, SiteVisit,
    Booking, Installment, Commission, Document, VerificationDocument,
    Communication, MessageTemplate
)


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'is_verified', 'territory', 'commission_rate', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'company_name', 'territory']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'agent', 'status', 'source', 'priority', 'property', 'created_at']
    list_filter = ['status', 'source', 'priority', 'created_at']
    search_fields = ['name', 'email', 'phone', 'agent__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LeadFollowUp)
class LeadFollowUpAdmin(admin.ModelAdmin):
    list_display = ['lead', 'agent', 'follow_up_type', 'scheduled_date', 'completed', 'created_at']
    list_filter = ['follow_up_type', 'completed', 'created_at']
    search_fields = ['lead__name', 'agent__username']
    readonly_fields = ['created_at']


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'property', 'agent', 'scheduled_date', 'status', 'created_at']
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['customer_name', 'customer_phone', 'property__title', 'agent__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'property', 'agent', 'status', 'total_amount', 'booking_date']
    list_filter = ['status', 'booking_date', 'created_at']
    search_fields = ['customer_name', 'customer_phone', 'property__title', 'agent__username']
    readonly_fields = ['booking_date', 'created_at', 'updated_at']


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'installment_number', 'amount', 'due_date', 'status', 'paid_date']
    list_filter = ['status', 'due_date', 'paid_date']
    search_fields = ['booking__customer_name', 'receipt_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['agent', 'booking', 'property', 'commission_amount', 'status', 'due_date', 'paid_date']
    list_filter = ['status', 'due_date', 'paid_date', 'created_at']
    search_fields = ['agent__username', 'booking__customer_name', 'property__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'category', 'property', 'agent', 'uploaded_at']
    list_filter = ['document_type', 'category', 'uploaded_at']
    search_fields = ['title', 'agent__username', 'property__title']
    readonly_fields = ['uploaded_at', 'file_size']


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'document_type', 'agent', 'status',
        'is_current', 'submitted_at', 'admin_reviewed_at'
    ]
    list_filter = ['status', 'document_type', 'is_current', 'submitted_at']
    search_fields = ['document_name', 'agent__username', 'agent__email']
    readonly_fields = ['submitted_at', 'updated_at', 'admin_reviewed_at']


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ['agent', 'communication_type', 'recipient', 'status', 'sent_at']
    list_filter = ['communication_type', 'status', 'sent_at']
    search_fields = ['agent__username', 'recipient', 'subject']
    readonly_fields = ['sent_at']


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'agent', 'template_type', 'purpose', 'is_active', 'created_at']
    list_filter = ['template_type', 'purpose', 'is_active', 'created_at']
    search_fields = ['name', 'agent__username']
    readonly_fields = ['created_at', 'updated_at']
