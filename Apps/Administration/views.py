from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Avg
from django.contrib.auth.models import User
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta
from .auth_utils import role_required
from .models import (
    AdminProfile, SystemSettings, DashboardWidget, UserPermission,
    ActivityLog, SystemBackup, SystemMaintenance, Report, GeneratedReport,
    Notification, SystemMetrics
)
from Apps.Customer.models import CustomerProfile, Inquiry, SavedProperty
from Apps.Investor.models import Investment, InvestmentListing, InvestorProfile
from Apps.PublicPage.models import Property
from .serializers import (
    AdminProfileSerializer, SystemSettingsSerializer, DashboardWidgetSerializer,
    UserPermissionSerializer, ActivityLogSerializer, SystemBackupSerializer,
    SystemMaintenanceSerializer, ReportSerializer, GeneratedReportSerializer,
    NotificationSerializer, SystemMetricsSerializer,
    CreateSystemSettingsSerializer, CreateDashboardWidgetSerializer,
    CreateUserPermissionSerializer, CreateSystemBackupSerializer,
    CreateSystemMaintenanceSerializer, CreateReportSerializer,
    CreateNotificationSerializer, CreateSystemMetricsSerializer
)


class AdminProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Only admin users can access admin profiles
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        profile, created = AdminProfile.objects.get_or_create(user=self.request.user)
        return profile


class SystemSettingsListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access system settings
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return SystemSettings.objects.all().order_by('setting_key')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSystemSettingsSerializer
        return SystemSettingsSerializer


class SystemSettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SystemSettings.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        # Only admin users can access system settings
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


class DashboardWidgetListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access dashboard widgets
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return DashboardWidget.objects.filter(is_active=True).order_by('display_order')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateDashboardWidgetSerializer
        return DashboardWidgetSerializer


class DashboardWidgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DashboardWidget.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        # Only admin users can access dashboard widgets
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


class UserPermissionListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access user permissions
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return UserPermission.objects.select_related('user', 'granted_by').order_by('-granted_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserPermissionSerializer
        return UserPermissionSerializer

    def perform_create(self, serializer):
        # Only admin users can create user permissions
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        serializer.save(granted_by=self.request.user)


class UserPermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = UserPermission.objects.select_related('user', 'granted_by')
    
    def get_object(self):
        obj = super().get_object()
        # Only admin users can access user permissions
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


class ActivityLogListView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'module', 'user']
    search_fields = ['description', 'user__username', 'module']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        # Only admin users can access activity logs
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return ActivityLog.objects.select_related('user').order_by('-timestamp')


class SystemBackupListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access system backups
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return SystemBackup.objects.select_related('created_by').order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSystemBackupSerializer
        return SystemBackupSerializer

    def perform_create(self, serializer):
        # Only admin users can create system backups
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        serializer.save(created_by=self.request.user)


class SystemBackupDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SystemBackupSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SystemBackup.objects.select_related('created_by')
    
    def get_object(self):
        obj = super().get_object()
        # Only admin users can access system backups
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


class SystemMaintenanceListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access system maintenance
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return SystemMaintenance.objects.select_related('performed_by').order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSystemMaintenanceSerializer
        return SystemMaintenanceSerializer

    def perform_create(self, serializer):
        # Only admin users can create system maintenance records
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        serializer.save(performed_by=self.request.user)


class SystemMaintenanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SystemMaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SystemMaintenance.objects.select_related('performed_by')
    
    def get_object(self):
        obj = super().get_object()
        # Only admin users can access system maintenance
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


class ReportListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access reports
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return Report.objects.filter(is_active=True).select_related('created_by').order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateReportSerializer
        return ReportSerializer

    def perform_create(self, serializer):
        # Only admin users can create reports
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        serializer.save(created_by=self.request.user)


class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Report.objects.select_related('created_by')
    
    def get_object(self):
        obj = super().get_object()
        # Only admin users can access reports
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


class GeneratedReportListView(generics.ListAPIView):
    serializer_class = GeneratedReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['report', 'file_format', 'generated_by']

    def get_queryset(self):
        # Only admin users can access generated reports
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return GeneratedReport.objects.select_related('report', 'generated_by').order_by('-generated_at')


class NotificationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access notifications
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return Notification.objects.select_related('created_by').order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateNotificationSerializer
        return NotificationSerializer

    def perform_create(self, serializer):
        # Only admin users can create notifications
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        serializer.save(created_by=self.request.user)


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.select_related('created_by')
    
    def get_object(self):
        obj = super().get_object()
        # Only admin users can access notifications
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


class SystemMetricsListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only admin users can access system metrics
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        return SystemMetrics.objects.order_by('-recorded_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSystemMetricsSerializer
        return SystemMetricsSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_dashboard(request):
    # Only admin users can access admin dashboard data
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    # Basic counts
    total_users = User.objects.count()
    total_customers = CustomerProfile.objects.count()
    total_investors = InvestorProfile.objects.count()
    total_properties = Property.objects.count()
    total_investments = Investment.objects.count()
    
    # Recent activity
    recent_inquiries = Inquiry.objects.order_by('-created_at')[:5]
    recent_investments = Investment.objects.order_by('-investment_date')[:5]
    recent_activity = ActivityLog.objects.order_by('-timestamp')[:10]
    
    # Statistics
    pending_inquiries = Inquiry.objects.filter(status='pending').count()
    active_investments = Investment.objects.filter(status='confirmed').count()
    total_investment_amount = Investment.objects.filter(status='confirmed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # System metrics
    system_metrics = SystemMetrics.objects.filter(
        recorded_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-recorded_at')[:20]
    
    data = {
        'counts': {
            'total_users': total_users,
            'total_customers': total_customers,
            'total_investors': total_investors,
            'total_properties': total_properties,
            'total_investments': total_investments,
        },
        'statistics': {
            'pending_inquiries': pending_inquiries,
            'active_investments': active_investments,
            'total_investment_amount': total_investment_amount,
        },
        'recent_data': {
            'inquiries': [
                {
                    'id': inquiry.id,
                    'subject': inquiry.subject,
                    'customer': inquiry.customer.username,
                    'created_at': inquiry.created_at,
                    'status': inquiry.status,
                } for inquiry in recent_inquiries
            ],
            'investments': [
                {
                    'id': investment.id,
                    'amount': investment.amount,
                    'investor': investment.investor.username,
                    'listing': investment.listing.title,
                    'investment_date': investment.investment_date,
                    'status': investment.status,
                } for investment in recent_investments
            ],
            'activity': ActivityLogSerializer(recent_activity, many=True).data,
        },
        'system_metrics': SystemMetricsSerializer(system_metrics, many=True).data,
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_management(request):
    # Only admin users can access user management
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    users = User.objects.all().order_by('-date_joined')
    
    user_data = []
    for user in users:
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
        }
        
        # Add profile information if exists
        if hasattr(user, 'customer_profile'):
            user_info['profile_type'] = 'customer'
        elif hasattr(user, 'investor_profile'):
            user_info['profile_type'] = 'investor'
        elif hasattr(user, 'admin_profile'):
            user_info['profile_type'] = 'admin'
        else:
            user_info['profile_type'] = None
            
        user_data.append(user_info)
    
    return Response(user_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def log_activity(request):
    # Only admin users can log system activities
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    action_type = request.data.get('action_type')
    module = request.data.get('module')
    description = request.data.get('description')
    
    if not all([action_type, module, description]):
        return Response(
            {'error': 'action_type, module, and description are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    activity = ActivityLog.objects.create(
        user=request.user,
        action_type=action_type,
        module=module,
        description=description,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    return Response(ActivityLogSerializer(activity).data, status=status.HTTP_201_CREATED)
