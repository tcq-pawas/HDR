from django.contrib import admin
from .models import CustomerProfile, Inquiry, SavedProperty, CustomerFeedback


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'preferred_contact_method', 'created_at']
    list_filter = ['preferred_contact_method', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['customer', 'subject', 'property', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['customer__username', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(SavedProperty)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display = ['customer', 'property', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['customer__username', 'property__title']
    readonly_fields = ['saved_at']
    date_hierarchy = 'saved_at'


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ['customer', 'property', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['customer__username', 'property__title', 'comment']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
