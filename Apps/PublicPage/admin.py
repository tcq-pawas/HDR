from django.contrib import admin
from .models import Property, PropertyImage, PropertyInquiry
from .models import ContactInquiry
from .models import WebsiteEnquiry, LocationData

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


admin.site.register(ContactInquiry)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    # list_display = ('title', 'price', 'location', 'property_type', 'is_featured', 'status', 'seller')
    list_display = ('title', 'location', 'category', 'price', 'project_size_acre', 'is_featured', 'status', 'is_admin_list')
    list_filter = ('status', 'property_type', 'is_featured', 'is_admin_list', 'created_at')
    search_fields = ('title', 'location', 'seller__username')
    inlines = [PropertyImageInline]
    prepopulated_fields = {'slug': ('title',)}
    actions = ['approve_properties', 'reject_properties']

    def save_model(self, request, obj, form, change):
        if not change:  # New property being created
            if not obj.seller:
                obj.seller = request.user
            from Apps.Administration.auth_utils import get_user_role
            user_role = get_user_role(request.user)
            if user_role == 'admin' or request.user.is_superuser or request.user.is_staff:
                obj.is_admin_list = True
        super().save_model(request, obj, form, change)

    @admin.action(description="Approve selected properties")
    def approve_properties(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description="Reject selected properties")
    def reject_properties(self, request, queryset):
        queryset.update(status='rejected')

@admin.register(PropertyInquiry)
class PropertyInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'related_property', 'created_at')
    search_fields = ('name', 'email', 'message')


@admin.register(WebsiteEnquiry)
class WebsiteEnquiryAdmin(admin.ModelAdmin):
    list_display = ('enquiry_id', 'full_name', 'email', 'status', 'created_at')
    search_fields = ('full_name', 'email', 'enquiry_id')


@admin.register(LocationData)
class LocationDataAdmin(admin.ModelAdmin):
    list_display = ('geo_name_id', 'city', 'state', 'country', 'sort_order', 'display_name')
    list_filter = ('state', 'country')
    search_fields = ('city', 'state', 'display_name')
    ordering = ('sort_order', 'city')
