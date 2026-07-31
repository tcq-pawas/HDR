from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.models import User
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta
from .auth_utils import role_required, admin_required_api
from .models import (
    AdminProfile, SystemSettings, DashboardWidget, UserPermission,
    ActivityLog, SystemBackup, SystemMaintenance, Report, GeneratedReport,
    Notification, SystemMetrics, PropertyReview
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from Apps.Customer.models import CustomerProfile, Inquiry, SavedProperty
from Apps.Investor.models import Investment, InvestmentListing, InvestorProfile
from .forms import InvestmentForm
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
    CreateNotificationSerializer, CreateSystemMetricsSerializer, AdminPropertyDetailSerializer,
    AdminPropertyListSerializer
    
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


@extend_schema(tags=['Administration'])
class SystemSettingsListCreateView(generics.ListCreateAPIView):
    """
    List and create system settings
    """
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


@extend_schema(tags=['Administration'])
class SystemSettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete system settings
    """
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


@extend_schema(tags=['Administration'])
class DashboardWidgetListCreateView(generics.ListCreateAPIView):
    """
    List and create dashboard widgets
    """
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


@extend_schema(tags=['Administration'])
class DashboardWidgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete dashboard widgets
    """
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


@extend_schema(tags=['Administration'])
class UserPermissionListCreateView(generics.ListCreateAPIView):
    """
    List and create user permissions
    """
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


@extend_schema(tags=['Administration'])
class UserPermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete user permissions
    """
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


@extend_schema(tags=['Administration'])
class ActivityLogListView(generics.ListAPIView):
    """
    List activity logs with filtering and search
    """
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


@login_required
def view_profile(request):
    from .auth_utils import get_user_role, get_role_based_redirect_url
    user_role = get_user_role(request.user)
    if user_role != 'admin':
        from django.contrib import messages
        messages.error(request, "Access denied. Admin access required.")
        return redirect(get_role_based_redirect_url(request.user))
    
    admin_profile, _ = AdminProfile.objects.get_or_create(
        user=request.user,
        defaults={'department': 'management', 'position': 'Administrator'}
    )
    context = {
        "user": request.user,
        "admin_profile": admin_profile,
    }
    return render(request, "administration/view_profile.html", context)


@login_required
def update_admin_profile(request):
    from .auth_utils import get_user_role, get_role_based_redirect_url
    user_role = get_user_role(request.user)
    if user_role != 'admin':
        from django.contrib import messages
        messages.error(request, "Access denied. Admin access required.")
        return redirect(get_role_based_redirect_url(request.user))
    
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone_number', '').strip()

        if username and username != user.username:
            from django.contrib.auth.models import User as UserModel
            if UserModel.objects.filter(username=username).exclude(pk=user.pk).exists():
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'message': 'Username already taken.'})
            user.username = username

        if email:
            user.email = email
        user.save()

        admin_profile, _ = AdminProfile.objects.get_or_create(
            user=user,
            defaults={'department': 'management', 'position': 'Administrator'}
        )
        if phone:
            admin_profile.phone = phone
        if 'profile_picture' in request.FILES:
            admin_profile.profile_picture = request.FILES['profile_picture']
        admin_profile.save()

        from django.http import JsonResponse
        return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})

    from django.http import JsonResponse
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

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
    
    was_inactive = not user.is_active
    user.is_active = True
    user.save()
    
    # Always verify the profile when the admin clicks activate/approve
    if hasattr(user, 'agent_profile'):
        user.agent_profile.is_verified = True
        user.agent_profile.verification_status = 'approved'
        user.agent_profile.save()
    elif hasattr(user, 'investor_profile'):
        user.investor_profile.verified = True
        user.investor_profile.save()
        
    # If the user was just approved/activated, send them the approval email with a password reset link
    if was_inactive:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        domain = request.get_host()
        reset_url = f"http://{domain}{reverse('auth:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
        
        html_message = f"""
        <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="background: linear-gradient(135deg, #0F766E 0%, #115E59 100%); padding: 30px 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 1px;">🌱 HeyDay Realty</h1>
            </div>
            <div style="padding: 40px 30px; background-color: #ffffff;">
                <h2 style="color: #1F2937; margin-top: 0; font-size: 22px;">Account Approved! 🎉</h2>
                <p style="color: #4B5563; font-size: 16px; line-height: 1.6;">Hello <strong>{user.first_name}</strong>,</p>
                <p style="color: #4B5563; font-size: 16px; line-height: 1.6;">Great news! Your account has been fully approved by our administration team.</p>
                <p style="color: #4B5563; font-size: 16px; line-height: 1.6;">You are now ready to set up your password and access your dedicated dashboard.</p>
                
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{reset_url}" style="background-color: #10B981; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);">Set Password & Login</a>
                </div>
                
                <p style="color: #6B7280; font-size: 14px; line-height: 1.5;">If the button doesn't work, copy and paste this link into your browser:<br><a href="{reset_url}" style="color: #0F766E; word-break: break-all;">{reset_url}</a></p>
                
                <p style="color: #4B5563; font-size: 16px; line-height: 1.6; margin-top: 30px;">Best regards,<br><strong style="color: #0F766E;">HeyDay Realty Team</strong></p>
            </div>
            <div style="background-color: #F9FAFB; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="color: #9CA3AF; font-size: 13px; margin: 0;">&copy; 2026 HeyDay Realty. All rights reserved.</p>
            </div>
        </div>
        """
        send_mail(
            subject='Account Approved - HeyDay Realty',
            message=f'Hello {user.first_name},\n\nGreat news! Your account has been approved by the administration team.\n\nPlease click the link below to set your password and log in to your dashboard:\n{reset_url}\n\nBest regards,\nHeyDay Realty Team',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    
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
    
    # Update to the new password
    new_password = request.data.get('new_password')
    if not new_password:
        return Response({'success': False, 'message': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    from django.contrib.auth.hashers import make_password
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
    
    return Response({'success': True, 'message': 'Password reset successfully!'})


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

@extend_schema(tags=['Properties'])
class PropertyReviewListView(generics.ListAPIView):
    """
    List all properties for admin review with filtering
    """
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


@extend_schema(tags=['Properties'])
class PropertyReviewDetailView(generics.RetrieveAPIView):
    """
    Get detailed property information for review
    """
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


@extend_schema(tags=['Properties'])
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


@extend_schema(tags=['Properties'])
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


@extend_schema(tags=['Properties'])
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

@api_view(['POST'])
@admin_required_api
def save_email_settings(request):
    try:
        from Apps.Administration.models import SystemSettings
        host = request.data.get('smtpHost')
        port = request.data.get('smtpPort')
        username = request.data.get('smtpUsername')
        password = request.data.get('smtpPassword')
        
        # We also want to support TLS, but UI doesn't have it explicitly right now, so we default to true or use port
        use_tls = 'true' if str(port) == '587' else 'false'
        
        SystemSettings.objects.update_or_create(setting_key='EMAIL_HOST', defaults={'setting_value': host})
        SystemSettings.objects.update_or_create(setting_key='EMAIL_PORT', defaults={'setting_value': port})
        SystemSettings.objects.update_or_create(setting_key='EMAIL_HOST_USER', defaults={'setting_value': username})
        SystemSettings.objects.update_or_create(setting_key='EMAIL_HOST_PASSWORD', defaults={'setting_value': password})
        SystemSettings.objects.update_or_create(setting_key='EMAIL_USE_TLS', defaults={'setting_value': use_tls})
        SystemSettings.objects.update_or_create(setting_key='DEFAULT_FROM_EMAIL', defaults={'setting_value': request.data.get('emailFrom', 'noreply@heydayrealty.com')})

        return Response({'success': True, 'message': 'Email settings saved successfully'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)

@api_view(['POST'])
@admin_required_api
def test_email_settings(request):
    try:
        from django.core.mail import send_mail
        from Apps.Administration.models import SystemSettings
        
        # Ensure latest settings are used by clearing any cached connection
        # We can just use send_mail, which will instantiate the backend with current DB settings
        send_mail(
            subject='Test Email from HeyDay Realty Admin',
            message='This is a test email to verify your SMTP settings are configured correctly.',
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=[request.user.email or request.data.get('testEmail', 'noreply@heydayrealty.com')],
            fail_silently=False,
        )
        return Response({'success': True, 'message': 'Test email sent successfully!'})
    except Exception as e:
        error_msg = str(e)
        if '535' in error_msg and 'Username and Password not accepted' in error_msg:
            error_msg = 'Google SMTP Authentication Failed: You are likely using your regular Google password. Google requires you to generate a 16-digit "App Password" to use SMTP. Please go to your Google Account -> Security -> 2-Step Verification -> App Passwords to generate one.'
        return Response({'success': False, 'message': error_msg}, status=400)


@api_view(['POST'])
@admin_required_api
def save_security_settings(request):
    try:
        from Apps.Administration.models import SystemSettings
        
        session_timeout = request.data.get('sessionTimeout', '30')
        max_login_attempts = request.data.get('maxLoginAttempts', '5')
        password_min_length = request.data.get('passwordMinLength', '8')
        require_two_factor = 'true' if request.data.get('requireTwoFactor') else 'false'
        password_complexity = 'true' if request.data.get('passwordComplexity') else 'false'
        login_notifications = 'true' if request.data.get('loginNotifications') else 'false'
        
        SystemSettings.objects.update_or_create(setting_key='SESSION_TIMEOUT', defaults={'setting_value': str(session_timeout)})
        SystemSettings.objects.update_or_create(setting_key='MAX_LOGIN_ATTEMPTS', defaults={'setting_value': str(max_login_attempts)})
        SystemSettings.objects.update_or_create(setting_key='MIN_PASSWORD_LENGTH', defaults={'setting_value': str(password_min_length)})
        SystemSettings.objects.update_or_create(setting_key='REQUIRE_TWO_FACTOR', defaults={'setting_value': require_two_factor})
        SystemSettings.objects.update_or_create(setting_key='PASSWORD_COMPLEXITY', defaults={'setting_value': password_complexity})
        SystemSettings.objects.update_or_create(setting_key='LOGIN_NOTIFICATIONS', defaults={'setting_value': login_notifications})

        return Response({'success': True, 'message': 'Security settings saved successfully'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(['POST'])
@admin_required_api
def save_general_settings(request):
    try:
        from Apps.Administration.models import SystemSettings

        username = request.data.get('username', '').strip()
        if username and username != request.user.username:
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
                return Response({'success': False, 'message': 'Username already taken.'}, status=400)
            request.user.username = username
            request.user.save()
        
        site_name = request.data.get('siteName', 'HeyDay Realty')
        site_description = request.data.get('siteDescription', 'Professional real estate investment platform')
        contact_email = request.data.get('contactEmail', 'info@heydayrealty.com')
        phone_number = request.data.get('phoneNumber', '+1 (555) 123-4567')
        address = request.data.get('address', '123 Business Ave, Suite 100\nNew York, NY 10001')
        timezone = request.data.get('timezone', 'America/New_York')
        
        SystemSettings.objects.update_or_create(setting_key='SITE_NAME', defaults={'setting_value': site_name})
        SystemSettings.objects.update_or_create(setting_key='SITE_DESCRIPTION', defaults={'setting_value': site_description})
        SystemSettings.objects.update_or_create(setting_key='CONTACT_EMAIL', defaults={'setting_value': contact_email})
        SystemSettings.objects.update_or_create(setting_key='PHONE_NUMBER', defaults={'setting_value': phone_number})
        SystemSettings.objects.update_or_create(setting_key='ADDRESS', defaults={'setting_value': address})
        SystemSettings.objects.update_or_create(setting_key='TIMEZONE', defaults={'setting_value': timezone})

        return Response({'success': True, 'message': 'General settings saved successfully'})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_inquiries(request):
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    from Apps.PublicPage.models import Inquiry as WebsiteContactInquiry
    
    unread_count = WebsiteContactInquiry.objects.filter(status='new').count()
    latest_new = WebsiteContactInquiry.objects.filter(status='new').order_by('-created_at')[:5]
    
    data = {
        'unread_count': unread_count,
        'latest_inquiries': [
            {
                'id': item.id,
                'enquiry_id': item.enquiry_id,
                'full_name': item.full_name,
                'phone_number': item.phone_number or '-',
                'email': item.email or '-',
                'investment_budget': item.investment_budget or '-',
                'message': item.message[:100] + '...' if len(item.message) > 100 else item.message,
                'status': item.status,
                'created_at': item.created_at.strftime('%d %b, %Y %I:%M %p'),
            } for item in latest_new
        ]
    }
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_investment(request):
    """API endpoint to create an investment"""
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
    
    form = InvestmentForm(request.data)
    
    if form.is_valid():
        investment = form.save()
        return Response({
            'success': True,
            'message': 'Investment created successfully',
            'investment': {
                'id': investment.id,
                'investor': investment.investor.username,
                'property': investment.listing.property_obj.title,
                'amount': str(investment.amount),
                'status': investment.status,
                'investment_date': investment.investment_date.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'success': False,
            'errors': form.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class AdminPropertyDetailAPIView(generics.RetrieveAPIView):
    """
    GET Admin Property Details API
    """
    serializer_class = AdminPropertyDetailSerializer
    def get_queryset(self):
        return Property.objects.filter(is_admin_list=True)
    
    
    
class AdminPropertyListAPIView(generics.ListAPIView):
    """
    GET list of ALL admin-added properties (no ID needed)
    """
    serializer_class = AdminPropertyListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Property.objects.filter(is_admin_list=True).order_by('-created_at')

# --- Document Verification / KYC Management ---

@login_required
def document_verification_list(request):
    """View to list all Agent KYC documents for Admin Review"""
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Admin access required.")
        
    from Apps.Agent.models import AgentProfile
    # Group profiles by status
    pending = AgentProfile.objects.filter(verification_status='pending').select_related('user').order_by('-user__date_joined')
    approved = AgentProfile.objects.filter(verification_status='approved').select_related('user').order_by('-user__date_joined')
    rejected = AgentProfile.objects.filter(verification_status='rejected').select_related('user').order_by('-user__date_joined')
    
    context = {
        'pending_profiles': pending,
        'approved_profiles': approved,
        'rejected_profiles': rejected,
        'page_title': "KYC Verifications",
    }
    return render(request, 'administration/document_verification_list.html', context)


@login_required
def approve_kyc(request, profile_id):
    """View to approve an agent's KYC documents"""
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        return JsonResponse({'success': False, 'message': 'Admin access required.'}, status=403)
        
    from Apps.Agent.models import AgentProfile
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.http import JsonResponse
    
    if request.method == 'POST':
        try:
            profile = AgentProfile.objects.get(id=profile_id)
            profile.verification_status = 'approved'
            profile.is_verified = True
            profile.save()
            
            # Activate pending subscription if it exists
            from Apps.Subscriptions.models import UserSubscription
            from django.utils import timezone
            from datetime import timedelta
            
            user_sub = UserSubscription.objects.filter(user=profile.user, status='pending').first()
            if user_sub:
                user_sub.status = 'active'
                user_sub.start_date = timezone.now()
                cycle_mapping = {'1M': 30, '3M': 90, '6M': 180, '12M': 365}
                days = cycle_mapping.get(user_sub.pricing.billing_cycle, 30) if user_sub.pricing else 30
                user_sub.end_date = timezone.now() + timedelta(days=days)
                user_sub.save()
            
            # Send Email
            subject = 'Your HeyDay Realty Account has been Approved!'
            html_message = render_to_string('administration/emails/kyc_approved.html', {'user': profile.user})
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to = profile.user.email
            
            if to:
                send_mail(subject, plain_message, from_email, [to], html_message=html_message, fail_silently=True)
                
            messages.success(request, f"{profile.user.get_full_name() or profile.user.username}'s documents have been approved.")
            return redirect('admin_dash:document_verification_list')
        except AgentProfile.DoesNotExist:
            messages.error(request, 'Agent profile not found.')
            return redirect('admin_dash:document_verification_list')
            
    return redirect('admin_dash:document_verification_list')


@login_required
def reject_kyc(request, profile_id):
    """View to reject an agent's KYC documents with a reason"""
    from .auth_utils import get_user_role
    if get_user_role(request.user) != 'admin':
        return JsonResponse({'success': False, 'message': 'Admin access required.'}, status=403)
        
    from Apps.Agent.models import AgentProfile
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.http import JsonResponse
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Rejection reason is required.')
            return redirect('administration:document_verification_list')
            
        try:
            profile = AgentProfile.objects.get(id=profile_id)
            profile.verification_status = 'rejected'
            profile.is_verified = False
            # Store the rejection reason if we want it in DB, but for now we just email it
            profile.save()
            
            # Send Email
            subject = 'Action Required: HeyDay Realty Document Verification'
            html_message = render_to_string('administration/emails/kyc_rejected.html', {
                'user': profile.user,
                'reason': reason
            })
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to = profile.user.email
            
            if to:
                send_mail(subject, plain_message, from_email, [to], html_message=html_message, fail_silently=True)
                
            messages.success(request, f"{profile.user.get_full_name() or profile.user.username}'s documents have been rejected.")
            return redirect('admin_dash:document_verification_list')
        except AgentProfile.DoesNotExist:
            messages.error(request, 'Agent profile not found.')
            return redirect('admin_dash:document_verification_list')
            
    return redirect('admin_dash:document_verification_list')