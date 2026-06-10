from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.models import User
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta
from .auth_utils import role_required
from .models import (
    AdminProfile, SystemSettings, DashboardWidget, UserPermission,
    ActivityLog, SystemBackup, SystemMaintenance, Report, GeneratedReport,
    Notification, SystemMetrics, PropertyReview
)
from Apps.Customer.models import CustomerProfile, Inquiry, SavedProperty
from Apps.Investor.models import Investment, InvestmentListing, InvestorProfile
from Apps.PublicPage.models import Property
from .serializers import (
    AdminProfileSerializer, SystemSettingsSerializer, DashboardWidgetSerializer,
    UserPermissionSerializer, ActivityLogSerializer, SystemBackupSerializer,
    SystemMaintenanceSerializer, ReportSerializer, GeneratedReportSerializer,
    NotificationSerializer, SystemMetricsSerializer, PropertyReviewSerializer,
    PropertyListSerializer, PropertyDetailSerializer,
    CreateSystemSettingsSerializer, CreateDashboardWidgetSerializer,
    CreateUserPermissionSerializer, CreateSystemBackupSerializer,
    CreateSystemMaintenanceSerializer, CreateReportSerializer,
    CreateNotificationSerializer, CreateSystemMetricsSerializer
)


class AdminProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
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
        
        # Add role information based on group membership
        user_info['role'] = get_user_role(user)
            
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def edit_user(request, user_id):
    # Only admin users can edit users
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update user fields
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.username = request.data.get('username', user.username)
    user.email = request.data.get('email', user.email)
    
    # Update phone number if it exists in the model
    if hasattr(user, 'phone_number'):
        user.phone_number = request.data.get('phone_number', user.phone_number)
    
    # Update status
    is_active = request.data.get('is_active')
    if is_active is not None:
        user.is_active = is_active == 'true'
    
    # Update email verified if it exists
    if hasattr(user, 'email_verified'):
        email_verified = request.data.get('email_verified')
        if email_verified is not None:
            user.email_verified = email_verified == 'true'
    
    # Update 2FA if it exists
    if hasattr(user, 'two_factor_enabled'):
        two_factor_enabled = request.data.get('two_factor_enabled')
        if two_factor_enabled is not None:
            user.two_factor_enabled = two_factor_enabled == 'true'
    
    # Update role
    new_role = request.data.get('role')
    if new_role:
        from .auth_utils import assign_user_group
        assign_user_group(user, new_role)
    
    user.save()
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='update',
        module='user_management',
        description=f'Updated user {user.username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    return Response({'success': True, 'message': 'User updated successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def suspend_user(request, user_id):
    # Only admin users can suspend users
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    user.is_active = False
    user.save()
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='suspend',
        module='user_management',
        description=f'Suspended user {user.username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    return Response({'success': True, 'message': 'User suspended successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def activate_user(request, user_id):
    # Only admin users can activate users
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    user.is_active = True
    user.save()
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='activate',
        module='user_management',
        description=f'Activated user {user.username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    return Response({'success': True, 'message': 'User activated successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reset_password(request, user_id):
    # Only admin users can reset passwords
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Generate a random password
    from django.contrib.auth.hashers import make_password
    import secrets
    import string
    new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    user.password = make_password(new_password)
    user.save()
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='reset_password',
        module='user_management',
        description=f'Reset password for user {user.username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    return Response({'success': True, 'message': f'Password reset successfully. New password: {new_password}'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_role(request, user_id):
    # Only admin users can change roles
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    new_role = request.data.get('new_role')
    if not new_role:
        return Response({'success': False, 'message': 'New role is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    from .auth_utils import assign_user_group
    assign_user_group(user, new_role)
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='change_role',
        module='user_management',
        description=f'Changed role for user {user.username} to {new_role}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    return Response({'success': True, 'message': 'User role changed successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def delete_user(request, user_id):
    # Only admin users can delete users
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        return Response({'success': False, 'message': 'You cannot delete your own account'}, status=status.HTTP_400_BAD_REQUEST)
    
    username = user.username
    user.delete()
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='delete',
        module='user_management',
        description=f'Deleted user {username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    return Response({'success': True, 'message': 'User deleted successfully'})


# ==================== Property Review Views ====================

class PropertyReviewListView(generics.ListAPIView):
    """List all properties for admin review with filtering"""
    serializer_class = PropertyListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'property_type', 'category', 'seller']
    search_fields = ['title', 'location', 'seller__username']
    ordering_fields = ['created_at', 'updated_at', 'price', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        # Only admin users can access property review
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        
        queryset = Property.objects.select_related('seller', 'assigned_agent').all()
        
        # Apply status filter from query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Apply property type filter
        property_type = self.request.query_params.get('property_type')
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        # Apply category filter
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Apply agent filter
        seller_id = self.request.query_params.get('seller')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        
        # Apply date range filter
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset


class PropertyReviewDetailView(generics.RetrieveAPIView):
    """Get detailed property information for review"""
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Property.objects.select_related('seller', 'assigned_agent', 'created_by', 'last_updated_by')

    def get_object(self):
        obj = super().get_object()
        # Only admin users can access property review details
        from .auth_utils import get_user_role
        if get_user_role(self.request.user) != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin access required.")
        return obj


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_property(request, property_id):
    """Approve a property listing"""
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response({'success': False, 'message': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update property status
    property_obj.status = 'approved'
    property_obj.save()
    
    # Create or update review record
    review, created = PropertyReview.objects.get_or_create(
        property=property_obj,
        defaults={
            'reviewed_by': request.user,
            'status': 'approved',
            'review_notes': request.data.get('review_notes', '')
        }
    )
    
    if not created:
        review.reviewed_by = request.user
        review.status = 'approved'
        review.review_notes = request.data.get('review_notes', '')
        review.rejection_reason = None
        review.save()
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='update',
        module='property_review',
        description=f'Approved property: {property_obj.title}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    # Send notification to the agent (seller)
    try:
        Notification.objects.create(
            title=f'Property Approved: {property_obj.title}',
            message=f'Your property "{property_obj.title}" has been approved and is now visible on the website.',
            notification_type='success',
            is_global=False,
            created_by=request.user,
        )
        notification = Notification.objects.latest('created_at')
        notification.target_users.add(property_obj.seller)
    except Exception as e:
        # Log notification error but don't fail the approval
        pass
    
    return Response({
        'success': True,
        'message': 'Property approved successfully',
        'property_id': property_obj.id,
        'status': 'approved'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_property(request, property_id):
    """Reject a property listing with reason"""
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    rejection_reason = request.data.get('rejection_reason')
    if not rejection_reason:
        return Response(
            {'success': False, 'message': 'Rejection reason is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response({'success': False, 'message': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update property status
    property_obj.status = 'rejected'
    property_obj.save()
    
    # Create or update review record
    review, created = PropertyReview.objects.get_or_create(
        property=property_obj,
        defaults={
            'reviewed_by': request.user,
            'status': 'rejected',
            'rejection_reason': rejection_reason,
            'review_notes': request.data.get('review_notes', '')
        }
    )
    
    if not created:
        review.reviewed_by = request.user
        review.status = 'rejected'
        review.rejection_reason = rejection_reason
        review.review_notes = request.data.get('review_notes', '')
        review.save()
    
    # Log the activity
    ActivityLog.objects.create(
        user=request.user,
        action_type='update',
        module='property_review',
        description=f'Rejected property: {property_obj.title}. Reason: {rejection_reason}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    # Send notification to the agent (seller)
    try:
        Notification.objects.create(
            title=f'Property Rejected: {property_obj.title}',
            message=f'Your property "{property_obj.title}" has been rejected. Reason: {rejection_reason}. Please update and resubmit.',
            notification_type='warning',
            is_global=False,
            created_by=request.user,
        )
        notification = Notification.objects.latest('created_at')
        notification.target_users.add(property_obj.seller)
    except Exception as e:
        # Log notification error but don't fail the rejection
        pass
    
    return Response({
        'success': True,
        'message': 'Property rejected successfully',
        'property_id': property_obj.id,
        'status': 'rejected',
        'rejection_reason': rejection_reason
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def property_review_stats(request):
    """Get property review statistics for admin dashboard"""
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    total_properties = Property.objects.count()
    pending_review = Property.objects.filter(status='pending').count()
    approved_properties = Property.objects.filter(status='approved').count()
    rejected_properties = Property.objects.filter(status='rejected').count()
    
    # Properties needing review (pending + resubmitted)
    needing_review = Property.objects.filter(
        status__in=['pending', 'rejected']
    ).count()
    
    # Recent submissions
    recent_submissions = Property.objects.select_related('seller').order_by('-created_at')[:10]
    
    # Properties by status
    properties_by_status = Property.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Properties by type
    properties_by_type = Property.objects.values('property_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Properties by category
    properties_by_category = Property.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent reviews
    recent_reviews = PropertyReview.objects.select_related(
        'property', 'reviewed_by', 'property__seller'
    ).order_by('-reviewed_at')[:10]
    
    data = {
        'summary': {
            'total_properties': total_properties,
            'pending_review': pending_review,
            'approved_properties': approved_properties,
            'rejected_properties': rejected_properties,
            'needing_review': needing_review,
        },
        'recent_submissions': PropertyListSerializer(recent_submissions, many=True).data,
        'properties_by_status': list(properties_by_status),
        'properties_by_type': list(properties_by_type),
        'properties_by_category': list(properties_by_category),
        'recent_reviews': PropertyReviewSerializer(recent_reviews, many=True).data,
    }
    
    return Response(data)
