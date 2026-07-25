from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, date
import re

from django.shortcuts import redirect
from Apps.Administration.smart_dashboard_views import AdminDashboardMixin
from Apps.Administration.auth_utils import get_user_role, role_required
from Apps.Administration.models import ActivityLog, SystemMetrics, UserPermission, PropertyReview
from Apps.Customer.models import CustomerProfile, Inquiry, SavedProperty, PropertyViewing
from Apps.Investor.models import InvestorProfile, Investment, InvestmentListing, ROIData
from Apps.PublicPage.models import Property
from Apps.PublicPage.models import ContactInquiry


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
        
        # Property review statistics
        context['property_review_stats'] = {
            'total_submitted': Property.objects.count(),
            'pending_review': Property.objects.filter(status='pending').count(),
            'approved_properties': Property.objects.filter(status='approved').count(),
            'rejected_properties': Property.objects.filter(status='rejected').count(),
            'needing_review': Property.objects.filter(status__in=['pending', 'rejected']).count(),
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
        
        # Subscription revenue & Global Ledger
        from Apps.Subscriptions.models import PaymentTransaction, LedgerEntry
        subscription_revenue = PaymentTransaction.objects.filter(
            status='SUCCESS', 
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['subscription_revenue'] = subscription_revenue
        
        context['global_ledger'] = LedgerEntry.objects.select_related('user').order_by('-created_at')[:10]
        context['global_transactions'] = PaymentTransaction.objects.select_related('user').order_by('-created_at')[:10]
        
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
        # Recent properties
        context['recent_properties'] = Property.objects.select_related('seller').order_by('-created_at')[:10]
        
        # Recent property submissions needing review
        context['pending_properties'] = Property.objects.select_related('seller').filter(
            status='pending'
        ).order_by('-created_at')[:5]
        
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
        
        # Lead analytics (uses ContactInquiry — the public website enquiry model)
        context['lead_analytics'] = {
            'new_leads': ContactInquiry.objects.filter(
                created_at__gte=thirty_days_ago
            ).count(),
            'converted_leads': ContactInquiry.objects.filter(
                status='converted',
                created_at__gte=thirty_days_ago
            ).count(),
            'lost_leads': ContactInquiry.objects.filter(
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
        customer_count = 0
        investor_count = 0
        admin_count = 0
        agent_count = 0
        owner_count = 0
        
        for user in users:
            user.role = get_user_role(user)
            users_with_roles.append(user)
            
            if user.role == 'customer':
                customer_count += 1
            elif user.role == 'investor':
                investor_count += 1
            elif user.role == 'admin':
                admin_count += 1
            elif user.role == 'agent':
                agent_count += 1
            elif user.role == 'owner':
                owner_count += 1
        
        context['users'] = users_with_roles
        context['total_users'] = users.count()
        context['groups'] = ['customer', 'investor', 'admin', 'agent', 'owner']
        
        # Add role counts
        context['customer_count'] = customer_count
        context['investor_count'] = investor_count
        context['admin_count'] = admin_count
        context['agent_count'] = agent_count
        context['owner_count'] = owner_count
        context['active_users_count'] = User.objects.filter(is_active=True).count()
        
        return context


class InquiryManagementView(AdminDashboardMixin, TemplateView):
    """Inquiry management view for admins with strict access control"""
    template_name = 'administration/inquiry_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from Apps.PublicPage.models import Inquiry as WebsiteContactInquiry
        from django.db.models import Q
        from django.utils import timezone
        from datetime import timedelta
        from django.core.paginator import Paginator
        
        enquiries = ContactInquiry.objects.all().order_by('-created_at')
        all_enquiries = ContactInquiry.objects.all()

        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            enquiries = enquiries.filter(
                Q(full_name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search) |
                Q(enquiry_id__icontains=search)
            )

        # Status filter
        status = self.request.GET.get('status', '')
        if status:
            enquiries = enquiries.filter(status=status)

        # Budget filter
        budget = self.request.GET.get('budget', '')
        if budget:
            enquiries = enquiries.filter(investment_budget=budget)

        # Date filter
        date_filter = self.request.GET.get('date_filter', '')
        now = timezone.now()
        if date_filter == 'today':
            enquiries = enquiries.filter(created_at__date=now.date())
        elif date_filter == 'week':
            enquiries = enquiries.filter(created_at__gte=now - timedelta(days=7))
        elif date_filter == 'month':
            enquiries = enquiries.filter(created_at__gte=now - timedelta(days=30))

         # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')  # default: latest first
        allowed_sort_fields = [
            'enquiry_id', '-enquiry_id',
            'full_name', '-full_name',
            'investment_budget', '-investment_budget',
            'status', '-status',
            'created_at', '-created_at',
        ]
        if sort_by not in allowed_sort_fields:
            sort_by = '-created_at'
        enquiries = enquiries.order_by(sort_by)

        # Pagination — 20 per page
        paginator = Paginator(enquiries, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        
        context['inquiries'] =  page_obj
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()

        context['total_count'] = all_enquiries.count()
        context['responded_count'] = all_enquiries.exclude(status='new').exclude(status='closed').exclude(status='spam').count()
        context['pending_count'] = all_enquiries.filter(status='new').count()
        context['today_count'] = all_enquiries.filter(created_at__date=timezone.now().date()).count()

        context['status_choices'] = ContactInquiry.STATUS_CHOICES
        context['search'] = search
        context['selected_status'] = status
        context['selected_budget'] = budget
        context['selected_date_filter'] = date_filter
        context['current_sort'] = sort_by
        
        # Get distinct budget values for filter dropdown
        budget_list = list(set(ContactInquiry.objects.exclude(
            budget__isnull=True
        ).exclude(budget='').values_list('budget', flat=True)))
        
        # Sort budgets - put "Below" first, then sort by size
        def budget_sort_key(budget_str):
            if 'below' in budget_str.lower() or 'under' in budget_str.lower():
                return (0, 0)
            # Extract first number from budget string for sorting
            numbers = re.findall(r'\d+', budget_str)
            if numbers:
                return (1, int(numbers[0]))
            return (2, budget_str)
        
        context['budget_choices'] = sorted(budget_list, key=budget_sort_key)

        return context


class InvestmentManagementView(AdminDashboardMixin, TemplateView):
    """Investment management view for admins with strict access control"""
    template_name = 'administration/investment_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .forms import InvestmentForm
        
        context['investments'] = Investment.objects.select_related(
            'investor', 'listing', 'listing__property_obj'
        ).order_by('-investment_date')
        
        context['investment_listings'] = InvestmentListing.objects.select_related(
            'property_obj'
        ).order_by('-created_at')
        
        context['form'] = InvestmentForm()
        
        # Calculate statistics
        all_investments = Investment.objects.all()
        context['total_investments'] = all_investments.count()
        context['total_amount'] = all_investments.aggregate(total=Sum('amount'))['total'] or 0
        context['pending_investments'] = all_investments.filter(status='pending').count()
        context['approved_investments'] = all_investments.filter(status='confirmed').count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import InvestmentForm
        from django.contrib import messages
        
        form = InvestmentForm(request.POST)
        
        if form.is_valid():
            investment = form.save()
            messages.success(
                request,
                f"Investment created successfully! {investment.investor.username} invested ${investment.amount} in {investment.listing.property_obj.title}"
            )
        else:
            messages.error(request, f"Error creating investment: {form.errors}")
        
        return redirect('admin_dash:investment-management-page')


class SystemSettingsView(AdminDashboardMixin, TemplateView):
    """System settings view for admins with strict access control"""
    template_name = 'administration/system_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .models import SystemSettings
        settings_qs = SystemSettings.objects.all()
        settings_dict = {s.setting_key: s.setting_value for s in settings_qs}
        context['settings'] = settings_dict
        
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


class UserProfileView(AdminDashboardMixin, TemplateView):
    """User profile view for admins with strict access control"""
    template_name = 'administration/user_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        
        # Get the user
        user = get_object_or_404(User, id=user_id)
        user.role = get_user_role(user)
        context['viewed_user'] = user
        
        # Recent activities for this user
        context['recent_activities'] = ActivityLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        
        # Login history fetched from ActivityLog where action_type is 'login'
        login_activities = ActivityLog.objects.filter(
            user=user, 
            action_type='login'
        ).order_by('-timestamp')[:10]
        
        login_history = []
        import re
        for activity in login_activities:
            # Check if there is location in the description (e.g., User logged in. Location: ...)
            location = "N/A"
            if activity.description and "Location: " in activity.description:
                location = activity.description.split("Location: ")[-1].strip()
            
            # Simple parsing for device
            device = "Unknown"
            if activity.user_agent:
                if 'Mobile' in activity.user_agent:
                    device = "Mobile"
                elif 'Windows' in activity.user_agent:
                    device = "Windows Desktop"
                elif 'Mac' in activity.user_agent:
                    device = "Mac"
                elif 'Linux' in activity.user_agent:
                    device = "Linux"
                else:
                    device = "Desktop"

            login_history.append({
                'timestamp': activity.timestamp,
                'ip_address': activity.ip_address,
                'device': device,
                'location': location,
                'successful': True,  # assuming log entries are only for successful logins
            })
            
        context['login_history'] = login_history
        
        # Role-specific data
        if user.role == 'customer':
            try:
                customer_profile = CustomerProfile.objects.get(user=user)
                context['customer_data'] = {
                    'purchased_properties': 0,  # Would come from property purchase tracking
                    'saved_properties': SavedProperty.objects.filter(customer=user).count(),
                    'inquiries': Inquiry.objects.filter(customer=user).count(),
                    'documents': 0,  # Would come from a document model
                }
            except CustomerProfile.DoesNotExist:
                context['customer_data'] = {
                    'purchased_properties': 0,
                    'saved_properties': 0,
                    'inquiries': 0,
                    'documents': 0,
                }
        
        elif user.role == 'investor':
            try:
                investor_profile = InvestorProfile.objects.get(user=user)
                investments = Investment.objects.filter(investor=user)
                context['investor_data'] = {
                    'total_investments': investments.aggregate(total=Sum('amount'))['total'] or 0,
                    'roi': ROIData.objects.filter(investment__investor=user).aggregate(
                        avg_roi=Avg('actual_roi_percentage')
                    )['avg_roi'] or 0,
                    'investment_count': investments.count(),
                    'documents': 0,  # Would come from a document model
                }
            except InvestorProfile.DoesNotExist:
                context['investor_data'] = {
                    'total_investments': 0,
                    'roi': 0,
                    'investment_count': 0,
                    'documents': 0,
                }
        
        elif user.role in ['agent', 'owner']:
            context['agent_data'] = {
                'assigned_properties': Property.objects.filter(assigned_agent=user).count(),
                'leads': 0,  # Would come from agent-specific lead tracking
                'customers': 0,  # Would come from agent-specific customer tracking
                'commission': 0,  # Would come from commission calculations
            }
        
        elif user.role == 'admin':
            context['admin_data'] = {
                'permissions': UserPermission.objects.filter(user=user).values_list('permission_level', flat=True),
                'activity_logs': ActivityLog.objects.filter(user=user).order_by('-timestamp')[:5],
            }
            
        # Fetch subscription data
        try:
            from Apps.Subscriptions.models import UserSubscription, LedgerEntry
            subscription = UserSubscription.objects.get(user=user)
            context['subscription'] = subscription
        except Exception:
            context['subscription'] = None
            
        # Fetch ledger data
        try:
            from Apps.Subscriptions.models import LedgerEntry
            ledger_entries = LedgerEntry.objects.filter(user=user).order_by('-created_at')[:20]
            context['ledger_entries'] = ledger_entries
            context['current_balance'] = ledger_entries[0].balance_after_transaction if ledger_entries else 0
        except Exception:
            context['ledger_entries'] = []
            context['current_balance'] = 0
        
        return context


class PropertyReviewCenterView(AdminDashboardMixin, TemplateView):
    """Property Review Center for admins with strict access control"""
    template_name = 'administration/property_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get ONLY agent-submitted properties (exclude admin-added listings)
        properties = Property.objects.select_related('seller', 'assigned_agent').filter(
            is_admin_list=False
        ).order_by('-created_at')
        
        # Apply filters
        status_filter = self.request.GET.get('status')
        if status_filter:
            properties = properties.filter(status=status_filter)
        
        property_type = self.request.GET.get('property_type')
        if property_type:
            properties = properties.filter(property_type=property_type)
        
        category = self.request.GET.get('category')
        if category:
            properties = properties.filter(category=category)
        
        seller_id = self.request.GET.get('seller')
        if seller_id:
            properties = properties.filter(seller_id=seller_id)
        
        context['properties'] = properties
        context['total_properties'] = properties.count()
        
        # Statistics — agent properties only
        agent_props = Property.objects.filter(is_admin_list=False)
        context['stats'] = {
            'total_submitted': agent_props.count(),
            'pending_review': agent_props.filter(status='pending').count(),
            'approved': agent_props.filter(status='approved').count(),
            'rejected': agent_props.filter(status='rejected').count(),
            'needing_review': agent_props.filter(status__in=['pending', 'rejected']).count(),
        }
        
        # Filter options
        context['status_choices'] = [
            ('', 'All Status'),
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ]
        
        context['property_type_choices'] = [
            ('', 'All Types'),
            ('sale', 'For Sale'),
            ('rent', 'For Rent'),
        ]
        
        context['category_choices'] = [
            ('', 'All Categories'),
            ('Apartments', 'Apartments / Condos'),
            ('Villas', 'Villas / Independent Houses'),
            ('Commercial', 'Commercial Properties'),
            ('Luxury', 'Luxury Properties'),
            ('Plots', 'Plots / Land'),
        ]
        
        # Get all agents for filter
        context['agents'] = User.objects.filter(groups__name='agent').order_by('username')
        
        return context


class AdminPropertyListView(AdminDashboardMixin, TemplateView):
    """List of properties added directly by admins (is_admin_list=True)"""
    template_name = 'administration/admin_property_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        properties = Property.objects.filter(is_admin_list=True).order_by('-created_at')

        status_filter = self.request.GET.get('status', '')
        if status_filter:
            properties = properties.filter(status=status_filter)

        context['properties'] = properties
        context['total_properties'] = properties.count()
        context['status_filter'] = status_filter
        return context


class CustomerListView(AdminDashboardMixin, TemplateView):
    """List of customers for admin management"""
    template_name = 'administration/customer_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        customers = User.objects.filter(groups__name='customer').select_related('customer_profile').order_by('-date_joined')

        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            customers = customers.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Status filter
        status = self.request.GET.get('status', '')
        if status == 'active':
            customers = customers.filter(is_active=True)
        elif status == 'inactive':
            customers = customers.filter(is_active=False)

        context['customers'] = customers
        context['total_customers'] = customers.count()
        context['search'] = search
        context['selected_status'] = status
        return context


class AgentListView(AdminDashboardMixin, TemplateView):
    """List of agents for admin management"""
    template_name = 'administration/agent_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        agents = User.objects.filter(groups__name='agent').order_by('-date_joined')

        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            agents = agents.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Status filter
        status = self.request.GET.get('status', '')
        if status == 'active':
            agents = agents.filter(is_active=True)
        elif status == 'inactive':
            agents = agents.filter(is_active=False)

        context['agents'] = agents
        context['total_agents'] = agents.count()
        context['search'] = search
        context['selected_status'] = status
        return context


class PropertyReviewDetailPageView(AdminDashboardMixin, TemplateView):
    """Detailed property review page for admins"""
    template_name = 'administration/property_review_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_id = kwargs.get('property_id')
        
        # Get the property with all related data
        property_obj = get_object_or_404(
            Property.objects.select_related(
                'seller', 'assigned_agent', 'created_by', 'last_updated_by'
            ),
            id=property_id
        )
        
        context['property'] = property_obj
        
        # Get property images
        from Apps.PublicPage.models import PropertyImage
        context['property_images'] = PropertyImage.objects.filter(property=property_obj)
        
        # Get review history
        context['review_history'] = PropertyReview.objects.filter(
            property=property_obj
        ).select_related('reviewed_by').order_by('-reviewed_at')
        
        # Get latest review
        latest_review = context['review_history'].first()
        context['latest_review'] = latest_review
        
        # Get agent profile if seller is an agent
        try:
            from Apps.Agent.models import AgentProfile
            context['agent_profile'] = AgentProfile.objects.get(user=property_obj.seller)
        except AgentProfile.DoesNotExist:
            context['agent_profile'] = None
        
        return context


class InquiryBulkActionView(AdminDashboardMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        from Apps.PublicPage.models import Inquiry as WebsiteContactInquiry

        selected_ids = request.POST.getlist('selected_ids')
        bulk_action = request.POST.get('bulk_action')
        queryset = ContactInquiry.objects.filter(id__in=selected_ids)

        # if bulk_action == 'mark_contacted':
        #     queryset.update(status='contacted')
        # elif bulk_action == 'mark_follow_up':
        #     queryset.update(status='follow_up')
        # elif bulk_action == 'mark_converted':
        #     queryset.update(status='converted')
        # elif bulk_action == 'mark_closed':
        #     queryset.update(status='closed')
        if bulk_action == 'delete':
            queryset.delete()

        return redirect('admin_dash:inquiry-management-page')


class InquiryExportCSVView(AdminDashboardMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # from Apps.PublicPage.models import Inquiry as ContactInquiry
        from django.http import HttpResponse
        import csv

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="enquiries.csv"'
        writer = csv.writer(response)
        writer.writerow(['Enquiry ID', 'Full Name', 'Phone', 'Email', 'Budget', 'Message', 'Status', 'Submitted At'])

        for e in ContactInquiry.objects.all().order_by('-created_at'):
            writer.writerow([
                e.enquiry_id, e.full_name, e.phone, e.email,
                e.budget, e.message, e.get_status_display(),
                e.created_at.strftime('%d %b %Y, %I:%M %p')
            ])
        return response


class InquiryExportExcelView(AdminDashboardMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # from Apps.PublicPage.models import Inquiry as ContactInquiry
        from django.http import HttpResponse
        import openpyxl # type: ignore

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Enquiries"
        ws.append(['Enquiry ID', 'Full Name', 'Phone', 'Email', 'Budget', 'Message', 'Status', 'Submitted At'])

        for e in ContactInquiry.objects.all().order_by('-created_at'):
            ws.append([
                e.enquiry_id, e.full_name, e.phone, e.email,
                e.budget, e.message, e.get_status_display(),
                e.created_at.strftime('%d %b %Y, %I:%M %p')
            ])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="enquiries.xlsx"'
        wb.save(response)
        return response

class InquiryDetailPageView(AdminDashboardMixin, TemplateView):
    
    """Detail view for a single website enquiry"""
    template_name = 'administration/inquiry_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # from Apps.PublicPage.models import Inquiry as ContactInquiry
        
        enquiry_pk = kwargs.get('pk')
        enquiry = get_object_or_404(ContactInquiry, pk=enquiry_pk)
        
        # Automatically mark as viewed
        if enquiry.status == "new":
            enquiry.status = "viewed"
            enquiry.save(update_fields=["status"])
    
        context['enquiry'] = enquiry
        context['status_choices'] = ContactInquiry.STATUS_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        
        from Apps.PublicPage.models import Inquiry as ContactInquiry
        from django.utils import timezone
        from django.http import JsonResponse

        enquiry = get_object_or_404(ContactInquiry, pk=kwargs.get('pk'))
        action = request.POST.get('action')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(ContactInquiry.STATUS_CHOICES):
                enquiry.status = new_status
                enquiry.save()
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        # 'new_status': new_status,
                        'new_status_display': enquiry.get_status_display()
                    })
            else:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

        elif action == 'add_note':
            note_text = request.POST.get('note', '').strip()
            if note_text:
                timestamp = timezone.now().strftime('%d %b %Y, %I:%M %p')
                admin_name = request.user.get_full_name() or request.user.username
                new_entry = f"[{timestamp} - {admin_name}] {note_text}"
                enquiry.admin_notes = (enquiry.admin_notes + "\n\n" + new_entry) if enquiry.admin_notes else new_entry
                enquiry.save()
                if is_ajax:
                    return JsonResponse({'success': True, 'admin_notes': enquiry.admin_notes})

        return redirect('admin_dash:inquiry-detail-page', pk=enquiry.pk)
    
    
class InquiryDeleteView(AdminDashboardMixin, TemplateView):

    def post(self, request, *args, **kwargs):
        # from Apps.PublicPage.models import Inquiry as ContactInquiry

        enquiry = get_object_or_404(ContactInquiry, pk=kwargs.get('pk'))
        enquiry.delete()

        return redirect('admin_dash:inquiry-management-page')

class AdminFinancialsView(AdminDashboardMixin, TemplateView):
    """View all financial data including Payment Transactions and Ledger Entries"""
    template_name = 'administration/admin_financials.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from Apps.Subscriptions.models import PaymentTransaction, UserSubscription
        context['transactions'] = PaymentTransaction.objects.select_related('user', 'subscription__plan').order_by('-created_at')
        context['subscriptions'] = UserSubscription.objects.select_related('user', 'plan', 'pricing').prefetch_related('transactions').order_by('-start_date')
        return context
