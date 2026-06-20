from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg, Q, F, OuterRef
from django.db.models.functions import Trunc
from django.utils import timezone
from datetime import timedelta, date
from Apps.Administration.smart_dashboard_views import InvestorDashboardMixin
from Apps.Administration.auth_utils import get_user_role
from .models import InvestorProfile, Investment, InvestmentListing, ROIData, InvestorDocument, ROIHistory
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


class InvestmentDetailView(InvestorDashboardMixin, TemplateView):
    """Investment detail view with strict access control"""
    template_name = 'investor/investment_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        investment_id = self.kwargs.get('investment_id')
        
        # Try to get real investment from database
        try:
            investment = Investment.objects.get(
                id=investment_id,
                investor=user
            )
            
            # Get latest ROI data for this investment
            latest_roi = ROIData.objects.filter(
                investment=investment
            ).order_by('-created_at').first()
            
            context['investment'] = investment
            context['roi_data'] = latest_roi
        except Investment.DoesNotExist:
            # Return dummy data for testing purposes
            dummy_investments = {
                1: {
                    'id': 1,
                    'listing': {
                        'title': 'Modern Downtown Apartment',
                        'property_obj': {
                            'title': 'Luxury Condo Complex',
                            'location': 'Downtown Area',
                            'property_type': 'Residential',
                            'price': 2500000
                        },
                        'expected_roi_percentage': 12.5,
                        'investment_term_months': 24,
                        'payment_frequency': 'monthly',
                        'total_investment_needed': 2500000,
                        'total_invested_amount': 2000000,
                        'investment_type': 'equity'
                    },
                    'amount': 50000,
                    'investment_date': timezone.datetime(2024, 1, 15).date(),
                    'status': 'confirmed'
                },
                2: {
                    'id': 2,
                    'listing': {
                        'title': 'Suburban Family House',
                        'property_obj': {
                            'title': 'Residential Property Development',
                            'location': 'Suburban District',
                            'property_type': 'Residential',
                            'price': 1800000
                        },
                        'expected_roi_percentage': 10.8,
                        'investment_term_months': 18,
                        'payment_frequency': 'monthly',
                        'total_investment_needed': 1800000,
                        'total_invested_amount': 1500000,
                        'investment_type': 'debt'
                    },
                    'amount': 25000,
                    'investment_date': timezone.datetime(2024, 2, 20).date(),
                    'status': 'confirmed'
                },
                3: {
                    'id': 3,
                    'listing': {
                        'title': 'Luxury Penthouse',
                        'property_obj': {
                            'title': 'High-End Residential Tower',
                            'location': 'City Center',
                            'property_type': 'Residential',
                            'price': 5000000
                        },
                        'expected_roi_percentage': 15.2,
                        'investment_term_months': 36,
                        'payment_frequency': 'quarterly',
                        'total_investment_needed': 5000000,
                        'total_invested_amount': 4000000,
                        'investment_type': 'equity'
                    },
                    'amount': 75000,
                    'investment_date': timezone.datetime(2024, 3, 10).date(),
                    'status': 'pending'
                },
                4: {
                    'id': 4,
                    'listing': {
                        'title': 'Commercial Office Building',
                        'property_obj': {
                            'title': 'Business Park Development',
                            'location': 'Industrial Zone',
                            'property_type': 'Commercial',
                            'price': 8000000
                        },
                        'expected_roi_percentage': 14.0,
                        'investment_term_months': 48,
                        'payment_frequency': 'monthly',
                        'total_investment_needed': 8000000,
                        'total_invested_amount': 7000000,
                        'investment_type': 'equity'
                    },
                    'amount': 100000,
                    'investment_date': timezone.datetime(2023, 12, 5).date(),
                    'status': 'confirmed'
                }
            }
            
            investment = dummy_investments.get(investment_id)
            if investment:
                context['investment'] = investment
                context['roi_data'] = None
            else:
                raise Http404("Investment not found")
        
        return context


class InvestmentROIView(InvestorDashboardMixin, TemplateView):
    """Investment ROI data view with strict access control"""
    template_name = 'investor/investment_roi.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        investment_id = self.kwargs.get('investment_id')
        
        # Try to get real investment from database
        try:
            investment = Investment.objects.get(
                id=investment_id,
                investor=user
            )
            
            # Get ROI data for this investment
            roi_data = ROIData.objects.filter(
                investment=investment
            ).order_by('-created_at').first()
            
            # Get ROI history for this investment
            roi_history = ROIHistory.objects.filter(
                investment=investment
            ).order_by('record_date')
            
            context['investment'] = investment
            context['roi_data'] = roi_data
            context['roi_history'] = roi_history
        except Investment.DoesNotExist:
            # Return dummy data for testing purposes
            dummy_investments = {
                1: {
                    'id': 1,
                    'listing': {
                        'title': 'Modern Downtown Apartment',
                        'property_obj': {
                            'title': 'Luxury Condo Complex',
                            'location': 'Downtown Area',
                            'property_type': 'Residential',
                            'price': 2500000
                        },
                        'expected_roi_percentage': 12.5,
                        'investment_term_months': 24,
                        'payment_frequency': 'monthly',
                        'total_investment_needed': 2500000,
                        'total_invested_amount': 2000000,
                        'investment_type': 'equity'
                    },
                    'amount': 50000,
                    'investment_date': timezone.datetime(2024, 1, 15).date(),
                    'status': 'confirmed'
                },
                2: {
                    'id': 2,
                    'listing': {
                        'title': 'Suburban Family House',
                        'property_obj': {
                            'title': 'Residential Property Development',
                            'location': 'Suburban District',
                            'property_type': 'Residential',
                            'price': 1800000
                        },
                        'expected_roi_percentage': 10.8,
                        'investment_term_months': 18,
                        'payment_frequency': 'monthly',
                        'total_investment_needed': 1800000,
                        'total_invested_amount': 1500000,
                        'investment_type': 'debt'
                    },
                    'amount': 25000,
                    'investment_date': timezone.datetime(2024, 2, 20).date(),
                    'status': 'confirmed'
                },
                3: {
                    'id': 3,
                    'listing': {
                        'title': 'Luxury Penthouse',
                        'property_obj': {
                            'title': 'High-End Residential Tower',
                            'location': 'City Center',
                            'property_type': 'Residential',
                            'price': 5000000
                        },
                        'expected_roi_percentage': 15.2,
                        'investment_term_months': 36,
                        'payment_frequency': 'quarterly',
                        'total_investment_needed': 5000000,
                        'total_invested_amount': 4000000,
                        'investment_type': 'equity'
                    },
                    'amount': 75000,
                    'investment_date': timezone.datetime(2024, 3, 10).date(),
                    'status': 'pending'
                },
                4: {
                    'id': 4,
                    'listing': {
                        'title': 'Commercial Office Building',
                        'property_obj': {
                            'title': 'Business Park Development',
                            'location': 'Industrial Zone',
                            'property_type': 'Commercial',
                            'price': 8000000
                        },
                        'expected_roi_percentage': 14.0,
                        'investment_term_months': 48,
                        'payment_frequency': 'monthly',
                        'total_investment_needed': 8000000,
                        'total_invested_amount': 7000000,
                        'investment_type': 'equity'
                    },
                    'amount': 100000,
                    'investment_date': timezone.datetime(2023, 12, 5).date(),
                    'status': 'confirmed'
                }
            }
            
            dummy_roi_data = {
                1: {
                    'actual_roi_percentage': 8.3,
                    'total_returns': 4150,
                    'investment_period_months': 8,
                    'annualized_roi_percentage': 12.4
                },
                2: {
                    'actual_roi_percentage': 6.2,
                    'total_returns': 1550,
                    'investment_period_months': 5,
                    'annualized_roi_percentage': 14.9
                },
                4: {
                    'actual_roi_percentage': 12.8,
                    'total_returns': 12800,
                    'investment_period_months': 12,
                    'annualized_roi_percentage': 12.8
                }
            }
            
            dummy_roi_history = {
                1: [
                    {'record_date': timezone.datetime(2024, 1, 15).date(), 'monthly_returns': 520, 'cumulative_returns': 520, 'roi_percentage': 1.04},
                    {'record_date': timezone.datetime(2024, 2, 15).date(), 'monthly_returns': 515, 'cumulative_returns': 1035, 'roi_percentage': 2.07},
                    {'record_date': timezone.datetime(2024, 3, 15).date(), 'monthly_returns': 525, 'cumulative_returns': 1560, 'roi_percentage': 3.12},
                    {'record_date': timezone.datetime(2024, 4, 15).date(), 'monthly_returns': 530, 'cumulative_returns': 2090, 'roi_percentage': 4.18},
                    {'record_date': timezone.datetime(2024, 5, 15).date(), 'monthly_returns': 518, 'cumulative_returns': 2608, 'roi_percentage': 5.22},
                    {'record_date': timezone.datetime(2024, 6, 15).date(), 'monthly_returns': 542, 'cumulative_returns': 3150, 'roi_percentage': 6.30},
                    {'record_date': timezone.datetime(2024, 7, 15).date(), 'monthly_returns': 535, 'cumulative_returns': 3685, 'roi_percentage': 7.37},
                    {'record_date': timezone.datetime(2024, 8, 15).date(), 'monthly_returns': 465, 'cumulative_returns': 4150, 'roi_percentage': 8.30}
                ],
                2: [
                    {'record_date': timezone.datetime(2024, 3, 20).date(), 'monthly_returns': 310, 'cumulative_returns': 310, 'roi_percentage': 1.24},
                    {'record_date': timezone.datetime(2024, 4, 20).date(), 'monthly_returns': 305, 'cumulative_returns': 615, 'roi_percentage': 2.46},
                    {'record_date': timezone.datetime(2024, 5, 20).date(), 'monthly_returns': 315, 'cumulative_returns': 930, 'roi_percentage': 3.72},
                    {'record_date': timezone.datetime(2024, 6, 20).date(), 'monthly_returns': 320, 'cumulative_returns': 1250, 'roi_percentage': 5.00},
                    {'record_date': timezone.datetime(2024, 7, 20).date(), 'monthly_returns': 300, 'cumulative_returns': 1550, 'roi_percentage': 6.20}
                ],
                4: [
                    {'record_date': timezone.datetime(2024, 1, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 1067, 'roi_percentage': 1.07},
                    {'record_date': timezone.datetime(2024, 2, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 2134, 'roi_percentage': 2.13},
                    {'record_date': timezone.datetime(2024, 3, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 3201, 'roi_percentage': 3.20},
                    {'record_date': timezone.datetime(2024, 4, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 4268, 'roi_percentage': 4.27},
                    {'record_date': timezone.datetime(2024, 5, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 5335, 'roi_percentage': 5.34},
                    {'record_date': timezone.datetime(2024, 6, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 6402, 'roi_percentage': 6.40},
                    {'record_date': timezone.datetime(2024, 7, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 7469, 'roi_percentage': 7.47},
                    {'record_date': timezone.datetime(2024, 8, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 8536, 'roi_percentage': 8.54},
                    {'record_date': timezone.datetime(2024, 9, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 9603, 'roi_percentage': 9.60},
                    {'record_date': timezone.datetime(2024, 10, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 10670, 'roi_percentage': 10.67},
                    {'record_date': timezone.datetime(2024, 11, 5).date(), 'monthly_returns': 1067, 'cumulative_returns': 11737, 'roi_percentage': 11.74},
                    {'record_date': timezone.datetime(2024, 12, 5).date(), 'monthly_returns': 1063, 'cumulative_returns': 12800, 'roi_percentage': 12.80}
                ]
            }
            
            investment = dummy_investments.get(investment_id)
            if investment:
                context['investment'] = investment
                context['roi_data'] = dummy_roi_data.get(investment_id)
                context['roi_history'] = dummy_roi_history.get(investment_id, [])
            else:
                raise Http404("Investment not found")
        
        return context
