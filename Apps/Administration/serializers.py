from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import (
    AdminProfile, SystemSettings, DashboardWidget, UserPermission,
    ActivityLog, SystemBackup, SystemMaintenance, Report, GeneratedReport,
    Notification, SystemMetrics, PropertyReview
)
from Apps.PublicPage.models import Property


class AdminProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = AdminProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'department',
                 'position', 'phone', 'is_super_admin', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'is_super_admin']


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['id', 'setting_key', 'setting_value', 'description', 'is_active',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = ['id', 'name', 'widget_type', 'title', 'description', 'data_source',
                 'config', 'is_active', 'display_order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserPermissionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    granted_by_name = serializers.CharField(source='granted_by.username', read_only=True)

    class Meta:
        model = UserPermission
        fields = ['id', 'user', 'username', 'module', 'permission_level', 'granted_by',
                 'granted_by_name', 'granted_at', 'expires_at', 'is_active']
        read_only_fields = ['granted_at', 'granted_by']


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'username', 'action_type', 'module', 'description',
                 'ip_address', 'user_agent', 'timestamp']
        read_only_fields = ['timestamp']


class SystemBackupSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SystemBackup
        fields = ['id', 'backup_type', 'file_path', 'file_size', 'status',
                 'created_by', 'created_by_name', 'created_at', 'completed_at', 'notes']
        read_only_fields = ['created_at', 'completed_at', 'created_by']


class SystemMaintenanceSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta:
        model = SystemMaintenance
        fields = ['id', 'maintenance_type', 'title', 'description', 'scheduled_start',
                 'scheduled_end', 'actual_start', 'actual_end', 'status',
                 'performed_by', 'performed_by_name', 'impact', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'performed_by']


class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'name', 'report_type', 'description', 'parameters', 'template',
                 'is_active', 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'created_by']


class GeneratedReportSerializer(serializers.ModelSerializer):
    report_name = serializers.CharField(source='report.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)

    class Meta:
        model = GeneratedReport
        fields = ['id', 'report', 'report_name', 'file_path', 'file_format',
                 'parameters_used', 'generated_by', 'generated_by_name',
                 'generated_at', 'expires_at']
        read_only_fields = ['generated_at', 'generated_by']


class NotificationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    target_users_list = serializers.SerializerMethodField()
    target_groups_list = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'target_users',
                 'target_users_list', 'target_groups', 'target_groups_list',
                 'is_global', 'is_active', 'created_by', 'created_by_name',
                 'created_at', 'expires_at']
        read_only_fields = ['created_at', 'created_by']

    def get_target_users_list(self, obj):
        return [user.username for user in obj.target_users.all()]

    def get_target_groups_list(self, obj):
        return [group.name for group in obj.target_groups.all()]


class SystemMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemMetrics
        fields = ['id', 'metric_name', 'metric_value', 'metric_unit', 'recorded_at', 'category']
        read_only_fields = ['recorded_at']


class CreateSystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['setting_key', 'setting_value', 'description', 'is_active']


class CreateDashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = ['name', 'widget_type', 'title', 'description', 'data_source',
                 'config', 'is_active', 'display_order']


class CreateUserPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermission
        fields = ['user', 'module', 'permission_level', 'expires_at']


class CreateSystemBackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemBackup
        fields = ['backup_type', 'file_path', 'file_size', 'notes']


class CreateSystemMaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemMaintenance
        fields = ['maintenance_type', 'title', 'description', 'scheduled_start',
                 'scheduled_end', 'impact']


class CreateReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['name', 'report_type', 'description', 'parameters', 'template', 'is_active']


class CreateNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type', 'target_users',
                 'target_groups', 'is_global', 'is_active', 'expires_at']


class CreateSystemMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemMetrics
        fields = ['metric_name', 'metric_value', 'metric_unit', 'category']


class PropertyReviewSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)
    property_id = serializers.IntegerField(source='property.id', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    seller_name = serializers.CharField(source='property.seller.username', read_only=True)
    
    class Meta:
        model = PropertyReview
        fields = ['id', 'property', 'property_title', 'property_id', 'reviewed_by',
                 'reviewed_by_name', 'status', 'rejection_reason', 'review_notes',
                 'reviewed_at', 'updated_at', 'previous_review', 'seller_name']
        read_only_fields = ['reviewed_at', 'updated_at', 'reviewed_by']


class PropertyListSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = ['id', 'title', 'slug', 'price', 'location', 'property_type', 
                 'property_type_display', 'category', 'category_display', 'status',
                 'status_display', 'seller', 'seller_name', 'featured_image',
                 'featured_image_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_featured_image_url(self, obj):
        if obj.featured_image:
            return obj.featured_image.url
        return None


class PropertyDetailSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    seller_email = serializers.CharField(source='seller.email', read_only=True)
    assigned_agent_name = serializers.CharField(source='assigned_agent.username', read_only=True, allow_null=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    area_unit_display = serializers.CharField(source='get_area_unit_display', read_only=True, allow_null=True)
    facing_display = serializers.CharField(source='get_facing_direction_display', read_only=True, allow_null=True)
    land_category_display = serializers.CharField(source='get_land_category_display', read_only=True, allow_null=True)
    furnishing_display = serializers.CharField(source='get_furnishing_status_display', read_only=True, allow_null=True)
    possession_display = serializers.CharField(source='get_possession_status_display', read_only=True, allow_null=True)
    featured_image_url = serializers.SerializerMethodField()
    property_video_url = serializers.SerializerMethodField()
    drone_video_url = serializers.SerializerMethodField()
    floor_plan_url = serializers.SerializerMethodField()
    registry_copy_url = serializers.SerializerMethodField()
    sale_deed_url = serializers.SerializerMethodField()
    mutation_url = serializers.SerializerMethodField()
    building_approval_url = serializers.SerializerMethodField()
    completion_certificate_url = serializers.SerializerMethodField()
    noc_url = serializers.SerializerMethodField()
    layout_plan_url = serializers.SerializerMethodField()
    property_brochure_url = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    latest_review = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by']
    
    def get_featured_image_url(self, obj):
        if obj.featured_image:
            return obj.featured_image.url
        return None
    
    def get_property_video_url(self, obj):
        if obj.property_video:
            return obj.property_video.url
        return None
    
    def get_drone_video_url(self, obj):
        if obj.drone_video:
            return obj.drone_video.url
        return None
    
    def get_floor_plan_url(self, obj):
        if obj.floor_plan:
            return obj.floor_plan.url
        return None
    
    def get_registry_copy_url(self, obj):
        if obj.registry_copy:
            return obj.registry_copy.url
        return None
    
    def get_sale_deed_url(self, obj):
        if obj.sale_deed:
            return obj.sale_deed.url
        return None
    
    def get_mutation_url(self, obj):
        if obj.mutation:
            return obj.mutation.url
        return None
    
    def get_building_approval_url(self, obj):
        if obj.building_approval:
            return obj.building_approval.url
        return None
    
    def get_completion_certificate_url(self, obj):
        if obj.completion_certificate:
            return obj.completion_certificate.url
        return None
    
    def get_noc_url(self, obj):
        if obj.noc:
            return obj.noc.url
        return None
    
    def get_layout_plan_url(self, obj):
        if obj.layout_plan:
            return obj.layout_plan.url
        return None
    
    def get_property_brochure_url(self, obj):
        if obj.property_brochure:
            return obj.property_brochure.url
        return None
    
    def get_images(self, obj):
        from Apps.PublicPage.models import PropertyImage
        images = PropertyImage.objects.filter(property=obj)
        return [{'id': img.id, 'image': img.image.url, 'category': img.category} for img in images if img.image]
    
    def get_latest_review(self, obj):
        review = obj.reviews.first()
        if review:
            return PropertyReviewSerializer(review).data
        return None
