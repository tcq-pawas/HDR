from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import (
    AdminProfile, SystemSettings, DashboardWidget, UserPermission,
    ActivityLog, SystemBackup, SystemMaintenance, Report, GeneratedReport,
    Notification, SystemMetrics
)


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
