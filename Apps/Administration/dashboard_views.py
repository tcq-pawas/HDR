from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, date
from Apps.Administration.smart_dashboard_views import AdminDashboardMixin
from Apps.Administration.auth_utils import get_user_role, role_required
from Apps.Administration.models import ActivityLog, SystemMetrics, UserPermission
from Apps.Customer.models import CustomerProfile, Inquiry, SavedProperty, PropertyViewing
from Apps.Investor.models import InvestorProfile, Investment, InvestmentListing, ROIData
from Apps.PublicPage.models import Property


class AdminDashboardView(AdminDashboardMixin, TemplateView):
    """Administration dashboard view with strict access control"""
    template_name = 'administration/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Current date and last login
        context['current_date'] = date.today()
        context['last_login'] = self.request.user.last_login if self.request.user.is_authenticated else timezone.now()
        
        # System overview statistics
        context['system_stats'] = {
            'total_users': User.objects.count(),
            'total_customers': CustomerProfile.objects.count(),
            'total_investors': InvestorProfile.objects.count(),
            'total_properties': Property.objects.count(),
            'total_investments': Investment.objects.count(),
            'total_investment_listings': InvestmentListing.objects.count(),
            'agent_count': User.objects.filter(groups__name='agent').count(),
        }
        
        # Business metrics and analytics
        confirmed_investments = Investment.objects.filter(status='confirmed')
        context['business_metrics'] = {
            'pending_inquiries': Inquiry.objects.filter(status='pending').count(),
            'active_investments': confirmed_investments.count(),
            'total_investment_amount': confirmed_investments.aggregate(total=Sum('amount'))['total'] or 0,
            'saved_properties_count': SavedProperty.objects.count(),
            'scheduled_viewings': PropertyViewing.objects.filter(status='scheduled').count(),
        }
        
        # Sales and revenue analytics
        thirty_days_ago = timezone.now() - timedelta(days=30)
        context['sales_analytics'] = {
            'monthly_investments': confirmed_investments.filter(
                investment_date__gte=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'monthly_investment_count': confirmed_investments.filter(
                investment_date__gte=thirty_days_ago
            ).count(),
            'average_investment_size': confirmed_investments.aggregate(
                avg=Avg('amount')
            )['avg'] or 0,
        }
        
        # Property analytics
        context['property_analytics'] = {
            'active_properties': Property.objects.filter(is_active=True).count(),
            'featured_properties': Property.objects.filter(is_featured=True).count(),
            'available_properties': Property.objects.filter(status='available').count(),
            'reserved_properties': Property.objects.filter(status='reserved').count(),
            'sold_properties': Property.objects.filter(status='sold').count(),
            'properties_by_type': Property.objects.values('property_type').annotate(
                count=Count('id')
            ).order_by('-count'),
            'average_property_price': Property.objects.aggregate(
                avg_price=Avg('price')
            )['avg_price'] or 0,
        }
        
        # Recent activities
        context['recent_activities'] = ActivityLog.objects.select_related('user').order_by('-timestamp')[:10]
        
        # Recent inquiries with full details
        context['recent_inquiries'] = Inquiry.objects.select_related(
            'customer', 'property'
        ).order_by('-created_at')[:5]
        
        # Recent investments with full details
        context['recent_investments'] = Investment.objects.select_related(
            'investor', 'listing', 'listing__property_obj'
        ).order_by('-investment_date')[:5]
        
        # User distribution by role with percentages
        total_users = User.objects.count()
        user_distribution = []
        for role_name in ['admin', 'investor', 'customer', 'agent']:
            count = User.objects.filter(groups__name=role_name).count()
            percentage = (count / total_users * 100) if total_users > 0 else 0
            user_distribution.append({
                'role': role_name, 
                'count': count, 
                'percentage': round(percentage, 1)
            })
        context['user_distribution'] = user_distribution
        
        # System metrics (last 7 days with trend analysis)
        seven_days_ago = timezone.now() - timedelta(days=7)
        system_metrics = SystemMetrics.objects.filter(
            recorded_at__gte=seven_days_ago
        ).order_by('-recorded_at')[:20]
        context['system_metrics'] = system_metrics
        
        # Investment performance analytics
        context['investment_performance'] = {
            'total_roi': ROIData.objects.aggregate(
                total=Sum('total_returns')
            )['total'] or 0,
            'active_roi_records': ROIData.objects.count(),
            'roi_by_investment_type': ROIData.objects.select_related('investment__listing').values(
                'investment__listing__investment_type'
            ).annotate(
                total_returns=Sum('total_returns'),
                count=Count('id')
            ).order_by('-total_returns'),
        }
        
        # Customer engagement metrics
        context['customer_engagement'] = {
            'total_inquiries': Inquiry.objects.count(),
            'inquiries_this_month': Inquiry.objects.filter(
                created_at__gte=thirty_days_ago
            ).count(),
            'conversion_rate': self._calculate_conversion_rate(),
            'top_customers': CustomerProfile.objects.annotate(
                inquiry_count=Count('user__inquiries'),
                investment_count=Count('user__investments')
            ).order_by('-inquiry_count')[:5],
        }
        
        # Growth metrics (month-over-month)
        context['growth_metrics'] = self._calculate_growth_metrics()
        
        # Lead analytics
        context['lead_analytics'] = {
            'new_leads': Inquiry.objects.filter(
                created_at__gte=thirty_days_ago
            ).count(),
            'converted_leads': Inquiry.objects.filter(
                status='converted',
                created_at__gte=thirty_days_ago
            ).count(),
            'lost_leads': Inquiry.objects.filter(
                status='lost',
                created_at__gte=thirty_days_ago
            ).count(),
        }
        
        # Chart data for JavaScript
        context['chart_data'] = {
            'customerCount': CustomerProfile.objects.count(),
            'investorCount': InvestorProfile.objects.count(),
            'adminCount': User.objects.filter(groups__name='admin').count(),
            'agentCount': User.objects.filter(groups__name='agent').count(),
        }
        
        return context
    
    def _calculate_conversion_rate(self):
        """Calculate inquiry to investment conversion rate"""
        total_inquiries = Inquiry.objects.count()
        if total_inquiries == 0:
            return 0
        
        # Count unique customers who made investments after inquiries
        customers_with_investments = User.objects.filter(
            investment__isnull=False
        ).distinct().count()
        
        return round((customers_with_investments / total_inquiries) * 100, 2)
    
    def _calculate_growth_metrics(self):
        """Calculate month-over-month growth metrics"""
        now = timezone.now()
        last_month_start = now.replace(day=1) - timedelta(days=32)
        last_month_end = now.replace(day=1) - timedelta(days=1)
        this_month_start = now.replace(day=1)
        
        # User growth
        last_month_users = User.objects.filter(
            date_joined__gte=last_month_start,
            date_joined__lte=last_month_end
        ).count()
        this_month_users = User.objects.filter(
            date_joined__gte=this_month_start
        ).count()
        
        # Investment growth
        last_month_investments = Investment.objects.filter(
            investment_date__gte=last_month_start,
            investment_date__lte=last_month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        this_month_investments = Investment.objects.filter(
            investment_date__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'user_growth': self._calculate_growth_percentage(last_month_users, this_month_users),
            'investment_growth': self._calculate_growth_percentage(last_month_investments, this_month_investments),
        }
    
    def _calculate_growth_percentage(self, last_period, this_period):
        """Calculate percentage growth between two periods"""
        if last_period == 0:
            return 100 if this_period > 0 else 0
        return round(((this_period - last_period) / last_period) * 100, 2)


class UserManagementView(AdminDashboardMixin, TemplateView):
    """User management view for admins with strict access control"""
    template_name = 'administration/user_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        users = User.objects.select_related(
            'customer_profile', 'investor_profile', 'admin_profile'
        ).order_by('-date_joined')
        
        # Add role information to each user
        users_with_roles = []
        for user in users:
            user.role = get_user_role(user)
            users_with_roles.append(user)
        
        context['users'] = users_with_roles
        context['total_users'] = users.count()
        context['groups'] = ['customer', 'investor', 'admin', 'agent']
        
        # Add role counts
        context['customer_count'] = User.objects.filter(groups__name='customer').count()
        context['investor_count'] = User.objects.filter(groups__name='investor').count()
        context['admin_count'] = User.objects.filter(groups__name='admin').count()
        context['agent_count'] = User.objects.filter(groups__name='agent').count()
        context['active_users_count'] = User.objects.filter(is_active=True).count()
        
        return context


class InquiryManagementView(AdminDashboardMixin, TemplateView):
    """Inquiry management view for admins with strict access control"""
    template_name = 'administration/inquiry_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['inquiries'] = Inquiry.objects.select_related(
            'customer', 'property'
        ).order_by('-created_at')
        
        context['pending_count'] = Inquiry.objects.filter(status='pending').count()
        
        return context


class InvestmentManagementView(AdminDashboardMixin, TemplateView):
    """Investment management view for admins with strict access control"""
    template_name = 'administration/investment_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['investments'] = Investment.objects.select_related(
            'investor', 'listing', 'listing__property_obj'
        ).order_by('-investment_date')
        
        context['investment_listings'] = InvestmentListing.objects.select_related(
            'property_obj'
        ).order_by('-created_at')
        
        return context


class SystemSettingsView(AdminDashboardMixin, TemplateView):
    """System settings view for admins with strict access control"""
    template_name = 'administration/system_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .models import SystemSettings
        context['settings'] = SystemSettings.objects.all().order_by('setting_key')
        
        return context


class ReportsView(AdminDashboardMixin, TemplateView):
    """Reports view for admins with strict access control"""
    template_name = 'administration/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .models import Report, GeneratedReport
        context['reports'] = Report.objects.filter(is_active=True).order_by('-created_at')
        context['generated_reports'] = GeneratedReport.objects.select_related(
            'report', 'generated_by'
        ).order_by('-generated_at')[:10]
        
        return context


class ActivityLogView(AdminDashboardMixin, TemplateView):
    """Activity log view for admins with strict access control"""
    template_name = 'administration/activity_log.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['activities'] = ActivityLog.objects.select_related('user').order_by('-timestamp')
        
        return context
