from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg, Q, F, OuterRef
from django.db.models.functions import Trunc
from django.utils import timezone
from datetime import timedelta, date
from Apps.Administration.smart_dashboard_views import InvestorDashboardMixin
from Apps.Administration.auth_utils import get_user_role
from .models import InvestorProfile, Investment, InvestmentListing, ROIData, InvestorDocument
from Apps.PublicPage.models import Property


class InvestorDashboardView(InvestorDashboardMixin, TemplateView):
    """Investor dashboard view with strict access control"""
    template_name = 'investor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create investor profile
        profile, created = InvestorProfile.objects.get_or_create(user=user)
        context['profile'] = profile
        
        # Investment statistics
        investments = Investment.objects.filter(investor=user)
        confirmed_investments = investments.filter(status='confirmed')
        pending_investments = investments.filter(status='pending')
        
        context['investment_stats'] = {
            'total_investments': investments.count(),
            'active_investments': confirmed_investments.count(),
            'pending_investments': pending_investments.count(),
            'total_invested_amount': confirmed_investments.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'average_investment_size': confirmed_investments.aggregate(
                avg=Avg('amount')
            )['avg'] or 0,
        }
        
        # ROI and returns analysis
        investor_roi_data = ROIData.objects.filter(
            investment__investor=user
        ).select_related('investment', 'investment__listing')
        
        context['roi_analysis'] = {
            'total_returns': investor_roi_data.aggregate(
                total=Sum('total_returns')
            )['total'] or 0,
            'total_roi_percentage': investor_roi_data.aggregate(
                avg_roi=Avg('actual_roi_percentage')
            )['avg_roi'] or 0,
            'active_roi_records': investor_roi_data.count(),
            'best_performing_investment': investor_roi_data.order_by('-actual_roi_percentage').first(),
            'monthly_returns': self._calculate_monthly_returns(investor_roi_data),
        }
        
        # Investment portfolio breakdown
        portfolio_breakdown = confirmed_investments.values(
            'listing__investment_type',
            'listing__property_obj__property_type'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            avg_amount=Avg('amount')
        ).order_by('-total_amount')
        
        context['portfolio_breakdown'] = list(portfolio_breakdown)
        
        # Properties invested in with detailed information
        context['invested_properties'] = confirmed_investments.select_related(
            'listing', 'listing__property_obj'
        ).annotate(
            property_title=F('listing__property_obj__title'),
            property_location=F('listing__property_obj__location'),
            property_type=F('listing__property_obj__property_type'),
            investment_type=F('listing__investment_type')
        ).order_by('-investment_date')
        
        # Sold vs remaining units analysis
        context['unit_analysis'] = self._analyze_unit_performance(confirmed_investments)
        
        # Recent investments with performance metrics
        context['recent_investments'] = investments.select_related(
            'listing', 'listing__property_obj'
        ).annotate(
            latest_roi=ROIData.objects.filter(
                investment=OuterRef('pk')
            ).order_by('-created_at')[:1].values('actual_roi_percentage')
        ).order_by('-investment_date')[:5]
        
        # Available investment opportunities (filtered for investor)
        context['available_opportunities'] = InvestmentListing.objects.filter(
            status='active', 
            featured=True
        ).select_related('property_obj').annotate(
            investor_has_invested=Count(
                'investments', 
                filter=Q(investments__investor=user)
            )
        ).order_by('-created_at')[:6]
        
        # Investment performance trends
        context['performance_trends'] = self._calculate_performance_trends(confirmed_investments)
        
        # Document management
        context['document_summary'] = {
            'total_documents': InvestorDocument.objects.filter(investor=user).count(),
            'recent_documents': InvestorDocument.objects.filter(
                investor=user
            ).order_by('-uploaded_at')[:3],
        }
        
        # Upcoming investment milestones
        context['upcoming_milestones'] = self._get_upcoming_milestones(confirmed_investments)
        
        return context
    
    def _calculate_monthly_returns(self, roi_data):
        """Calculate monthly returns for the last 6 months"""
        six_months_ago = timezone.now() - timedelta(days=180)
        recent_roi = roi_data.filter(created_at__gte=six_months_ago)
        
        monthly_data = {}
        for roi in recent_roi:
            month_key = roi.created_at.strftime('%b %Y')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'returns': 0, 'count': 0}
            monthly_data[month_key]['returns'] += roi.total_returns
            monthly_data[month_key]['count'] += 1
        
        # Add average and trend to each month
        for month in monthly_data:
            count = monthly_data[month]['count']
            if count > 0:
                monthly_data[month]['average'] = monthly_data[month]['returns'] / count
            else:
                monthly_data[month]['average'] = 0
            # Simple trend calculation (up if more than previous month)
            monthly_data[month]['trend'] = 'stable'  # Placeholder for trend logic
        
        return monthly_data
    
    def _analyze_unit_performance(self, confirmed_investments):
        """Analyze sold vs remaining units for investor's properties"""
        unit_analysis = []
        
        for investment in confirmed_investments.select_related('listing', 'listing__property_obj'):
            listing = investment.listing
            property_obj = listing.property_obj
            
            # Calculate investment participation based on amount vs total needed
            total_investment_needed = listing.total_investment_needed
            investor_amount = investment.amount
            total_invested_amount = listing.total_invested_amount
            
            # Calculate investor's percentage of this investment
            investor_percentage = (investor_amount / total_investment_needed * 100) if total_investment_needed > 0 else 0
            
            # Calculate how much of the investment is filled
            investment_filled_percentage = (total_invested_amount / total_investment_needed * 100) if total_investment_needed > 0 else 0
            
            unit_analysis.append({
                'property_title': property_obj.title,
                'investment_type': listing.investment_type,
                'total_investment_needed': total_investment_needed,
                'total_invested_amount': total_invested_amount,
                'investor_amount': investor_amount,
                'investor_percentage': round(investor_percentage, 2),
                'investment_filled_percentage': round(investment_filled_percentage, 2),
                'remaining_amount': total_investment_needed - total_invested_amount,
                'investment_date': investment.investment_date,
            })
        
        return unit_analysis
    
    def _calculate_performance_trends(self, confirmed_investments):
        """Calculate investment performance trends over time"""
        trends = {
            'investment_growth': [],
            'roi_trend': [],
        }
        
        # Investment growth over last 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_investments = confirmed_investments.filter(
            investment_date__gte=six_months_ago
        ).annotate(
            month=Trunc('investment_date', 'month')
        ).values('month').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('month')
        
        trends['investment_growth'] = list(monthly_investments)
        
        # ROI trend (simplified - would need more detailed ROI data)
        investor_roi = ROIData.objects.filter(
            investment__investor=self.request.user
        ).annotate(
            month=Trunc('created_at', 'month')
        ).values('month').annotate(
            avg_roi=Avg('actual_roi_percentage'),
            total_returns=Sum('total_returns')
        ).order_by('month')[:6]
        
        trends['roi_trend'] = list(investor_roi)
        
        return trends
    
    def _get_upcoming_milestones(self, confirmed_investments):
        """Get upcoming investment milestones and important dates"""
        milestones = []
        
        for investment in confirmed_investments.select_related('listing'):
            listing = investment.listing
            
            # Add various milestones based on investment
            milestones.extend([
                {
                    'type': 'investment_anniversary',
                    'title': f'Investment Anniversary - {listing.property_obj.title}',
                    'date': investment.investment_date + timedelta(days=365),
                    'investment': investment,
                },
                {
                    'type': 'expected_returns',
                    'title': f'Expected Returns - {listing.property_obj.title}',
                    'date': investment.investment_date + timedelta(days=listing.investment_term_months * 30 or 365),
                    'investment': investment,
                },
            ])
        
        # Filter and sort upcoming milestones (next 90 days)
        ninety_days_ahead = timezone.now() + timedelta(days=90)
        upcoming = [m for m in milestones if m['date'] <= ninety_days_ahead]
        return sorted(upcoming, key=lambda x: x['date'])[:5]


class InvestorProfileView(InvestorDashboardMixin, TemplateView):
    """Investor profile management view with strict access control"""
    template_name = 'investor/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        profile, created = InvestorProfile.objects.get_or_create(user=user)
        context['profile'] = profile
        context['created'] = created
        
        return context


class InvestorInvestmentsView(InvestorDashboardMixin, TemplateView):
    """Investor investments management view with strict access control"""
    template_name = 'investor/investments.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['investments'] = Investment.objects.filter(
            investor=user
        ).select_related('listing', 'listing__property_obj').order_by('-investment_date')
        
        return context


class InvestorListingsView(InvestorDashboardMixin, TemplateView):
    """Investor available listings view with strict access control"""
    template_name = 'investor/listings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['listings'] = InvestmentListing.objects.filter(
            status='active'
        ).select_related('property_obj').annotate(
            investor_has_invested=Count(
                'investments', 
                filter=Q(investments__investor=user)
            )
        ).order_by('-created_at')
        
        return context


class InvestorROIDataView(InvestorDashboardMixin, TemplateView):
    """Investor ROI data view with strict access control"""
    template_name = 'investor/roi_data.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['roi_data'] = ROIData.objects.filter(
            investment__investor=user
        ).select_related('investment', 'investment__listing', 'investment__listing__property_obj').order_by('-created_at')
        
        # Calculate actual ROI analysis from real data
        total_returns = context['roi_data'].aggregate(total=Sum('total_returns'))['total'] or 0
        avg_roi = context['roi_data'].aggregate(avg=Avg('actual_roi_percentage'))['avg'] or 0
        
        context['roi_analysis'] = {
            'total_returns': total_returns,
            'total_roi_percentage': avg_roi,
            'active_roi_records': context['roi_data'].count(),
            'monthly_returns': self._calculate_monthly_returns(context['roi_data']),
        }
        
        # Get top performing investments from actual data
        context['top_performing'] = list(
            context['roi_data'].order_by('-actual_roi_percentage')[:5]
        )
        
        return context
    
    def _calculate_monthly_returns(self, roi_data):
        """Calculate monthly returns for the last 6 months"""
        six_months_ago = timezone.now() - timedelta(days=180)
        recent_roi = roi_data.filter(created_at__gte=six_months_ago)
        
        monthly_data = {}
        for roi in recent_roi:
            month_key = roi.created_at.strftime('%b %Y')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'returns': 0, 'count': 0}
            monthly_data[month_key]['returns'] += roi.total_returns
            monthly_data[month_key]['count'] += 1
        
        # Add average and trend to each month
        for month in monthly_data:
            count = monthly_data[month]['count']
            if count > 0:
                monthly_data[month]['average'] = monthly_data[month]['returns'] / count
            else:
                monthly_data[month]['average'] = 0
            # Simple trend calculation (up if more than previous month)
            monthly_data[month]['trend'] = 'stable'  # Placeholder for trend logic
        
        return monthly_data


class InvestorDocumentsView(InvestorDashboardMixin, TemplateView):
    """Investor documents management view with strict access control"""
    template_name = 'investor/documents.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['documents'] = InvestorDocument.objects.filter(
            investor=user
        ).order_by('-uploaded_at')
        
        return context
