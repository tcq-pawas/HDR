from django.contrib import admin
from .models import Property, PropertyImage, PropertyInquiry

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'location', 'property_type', 'is_featured', 'status', 'seller')
    list_filter = ('status', 'property_type', 'is_featured', 'created_at')
    search_fields = ('title', 'location', 'seller__username')
    inlines = [PropertyImageInline]
    prepopulated_fields = {'slug': ('title',)}
    actions = ['approve_properties', 'reject_properties']

    @admin.action(description="Approve selected properties")
    def approve_properties(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description="Reject selected properties")
    def reject_properties(self, request, queryset):
        queryset.update(status='rejected')

@admin.register(PropertyInquiry)
class PropertyInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'property', 'created_at')
    search_fields = ('name', 'email', 'message')
