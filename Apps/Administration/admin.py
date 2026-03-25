from django.contrib import admin
from .models import (
    AdminProfile, SystemSettings, DashboardWidget, UserPermission,
    ActivityLog, SystemBackup, SystemMaintenance, Report, GeneratedReport,
    Notification, SystemMetrics
)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'position', 'is_super_admin', 'created_at']
    list_filter = ['department', 'is_super_admin', 'created_at']
    search_fields = ['user__username', 'user__email', 'position']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['setting_key', 'setting_value', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['setting_key', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'title', 'is_active', 'display_order', 'created_at']
    list_filter = ['widget_type', 'is_active', 'created_at']
    search_fields = ['name', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['display_order', 'is_active']


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'permission_level', 'is_active', 'granted_at', 'expires_at']
    list_filter = ['permission_level', 'module', 'is_active', 'granted_at']
    search_fields = ['user__username', 'module']
    readonly_fields = ['granted_at']
    date_hierarchy = 'granted_at'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'module', 'timestamp', 'ip_address']
    list_filter = ['action_type', 'module', 'timestamp']
    search_fields = ['user__username', 'description', 'module']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(SystemBackup)
class SystemBackupAdmin(admin.ModelAdmin):
    list_display = ['backup_type', 'file_path', 'file_size', 'status', 'created_by', 'created_at']
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['file_path', 'notes']
    readonly_fields = ['created_at', 'completed_at', 'created_by']
    date_hierarchy = 'created_at'


@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['title', 'maintenance_type', 'scheduled_start', 'scheduled_end', 'status', 'performed_by']
    list_filter = ['maintenance_type', 'status', 'scheduled_start']
    search_fields = ['title', 'description', 'impact']
    readonly_fields = ['created_at', 'updated_at', 'performed_by']
    date_hierarchy = 'scheduled_start'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    date_hierarchy = 'created_at'


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['report', 'file_format', 'generated_by', 'generated_at', 'expires_at']
    list_filter = ['file_format', 'generated_at']
    search_fields = ['report__name', 'file_path']
    readonly_fields = ['generated_at', 'generated_by']
    date_hierarchy = 'generated_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'is_global', 'is_active', 'created_by', 'created_at']
    list_filter = ['notification_type', 'is_global', 'is_active', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'created_by']
    filter_horizontal = ['target_users', 'target_groups']
    date_hierarchy = 'created_at'


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_value', 'metric_unit', 'category', 'recorded_at']
    list_filter = ['category', 'metric_name', 'recorded_at']
    search_fields = ['metric_name', 'category']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'
    ordering = ['-recorded_at']
