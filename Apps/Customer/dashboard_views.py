from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from Apps.Administration.smart_dashboard_views import CustomerDashboardMixin
from Apps.Administration.auth_utils import get_user_role, role_required
from .models import CustomerProfile, Inquiry, SavedProperty, PropertyViewing
from Apps.PublicPage.models import Property


class CustomerDashboardView(CustomerDashboardMixin, TemplateView):
    """Customer dashboard view with strict access control"""
    template_name = 'customer/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create customer profile
        profile, created = CustomerProfile.objects.get_or_create(user=user)
        context['profile'] = profile
        
        # Personal purchase statistics
        context['purchase_stats'] = {
            'total_inquiries': Inquiry.objects.filter(customer=user).count(),
            'pending_inquiries': Inquiry.objects.filter(customer=user, status='pending').count(),
            'saved_properties': SavedProperty.objects.filter(customer=user).count(),
            'scheduled_viewings': PropertyViewing.objects.filter(
                customer=user, status='scheduled'
            ).count(),
            'completed_viewings': PropertyViewing.objects.filter(
                customer=user, status='completed'
            ).count(),
        }
        
        # Owned properties (if customer has made purchases)
        context['owned_properties'] = self._get_owned_properties(user)
        
        # Property interests and preferences
        context['property_interests'] = self._analyze_property_interests(user)
        
        # Recent activities
        context['recent_inquiries'] = Inquiry.objects.filter(
            customer=user
        ).select_related('property').order_by('-created_at')[:5]
        
        context['recent_saved_properties'] = SavedProperty.objects.filter(
            customer=user
        ).select_related('property').order_by('-saved_at')[:5]
        
        context['upcoming_viewings'] = PropertyViewing.objects.filter(
            customer=user, status='scheduled'
        ).select_related('property').order_by('scheduled_date')[:5]
        
        # Personal documents and papers (placeholder for future document management)
        context['document_summary'] = {
            'total_documents': 0,  # Placeholder until CustomerDocument model is created
            'recent_documents': [],  # Placeholder
            'pending_documents': 0,  # Placeholder
        }
        
        # Property location preferences analysis
        context['location_analysis'] = self._analyze_location_preferences(user)
        
        # Property type preferences
        context['property_type_analysis'] = self._analyze_property_type_preferences(user)
        
        # Budget analysis
        context['budget_analysis'] = self._analyze_budget_preferences(user)
        
        # Activity timeline
        context['activity_timeline'] = self._create_activity_timeline(user)
        
        # Recommended properties based on preferences
        context['recommended_properties'] = self._get_recommended_properties(user)
        
        # Available properties (limited data for public view)
        context['featured_properties'] = Property.objects.filter(
            is_featured=True, is_active=True
        ).values('id', 'title', 'price', 'location', 'property_type', 'area_sqft')[:6]
        
        return context
    
    def _get_owned_properties(self, user):
        """Get properties owned by the customer"""
        # This would typically come from a purchase/investment model
        # For now, we'll use inquiries that have been resolved (as potential purchases)
        purchased_properties = Inquiry.objects.filter(
            customer=user, 
            status='resolved'
        ).select_related('property').annotate(
            purchase_date=F('updated_at'),
            property_title=F('property__title'),
            property_location=F('property__location'),
            property_area=F('property__area_sqft'),
            property_price=F('property__price'),
            property_type=F('property__property_type')
        )
        
        return purchased_properties
    
    def _analyze_property_interests(self, user):
        """Analyze customer's property interests and preferences"""
        saved_properties = SavedProperty.objects.filter(customer=user).select_related('property')
        
        # Analyze by property type
        type_analysis = saved_properties.values('property__property_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Analyze by location
        location_analysis = saved_properties.values('property__location').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Analyze price range preferences
        avg_price = saved_properties.aggregate(
            avg_price=Avg('property__price')
        )['avg_price'] or 0
        
        price_ranges = {
            'min_price': float(avg_price) * 0.8 if avg_price else 0,
            'avg_price': float(avg_price) if avg_price else 0,
            'max_price': float(avg_price) * 1.2 if avg_price else 0,
        }
        
        return {
            'property_types': list(type_analysis),
            'preferred_locations': list(location_analysis),
            'price_preferences': price_ranges,
            'total_saved': saved_properties.count(),
        }
    
    def _analyze_location_preferences(self, user):
        """Analyze customer's location preferences"""
        inquiries = Inquiry.objects.filter(customer=user).select_related('property')
        saved = SavedProperty.objects.filter(customer=user).select_related('property')
        
        # Combine inquiries and saved properties for analysis
        all_properties = list(inquiries) + list(saved)
        
        location_data = {}
        for item in all_properties:
            property_obj = item.property if hasattr(item, 'property') else item.property
            location = property_obj.location
            
            if location not in location_data:
                location_data[location] = {
                    'inquiries': 0,
                    'saved': 0,
                    'viewings': 0,
                    'properties': set()
                }
            
            if hasattr(item, 'status'):  # It's an inquiry
                location_data[location]['inquiries'] += 1
            else:  # It's a saved property
                location_data[location]['saved'] += 1
            
            location_data[location]['properties'].add(property_obj.id)
        
        # Convert sets to counts and sort by total interest
        location_analysis = []
        for location, data in location_data.items():
            total_interest = data['inquiries'] + data['saved']
            location_analysis.append({
                'location': location,
                'inquiries': data['inquiries'],
                'saved': data['saved'],
                'total_interest': total_interest,
                'unique_properties': len(data['properties']),
            })
        
        return sorted(location_analysis, key=lambda x: x['total_interest'], reverse=True)[:5]
    
    def _analyze_property_type_preferences(self, user):
        """Analyze customer's property type preferences"""
        inquiries = Inquiry.objects.filter(customer=user).select_related('property')
        saved = SavedProperty.objects.filter(customer=user).select_related('property')
        
        type_data = {}
        for item in list(inquiries) + list(saved):
            property_obj = item.property if hasattr(item, 'property') else item.property
            prop_type = property_obj.property_type
            
            if prop_type not in type_data:
                type_data[prop_type] = {'inquiries': 0, 'saved': 0}
            
            if hasattr(item, 'status'):  # It's an inquiry
                type_data[prop_type]['inquiries'] += 1
            else:  # It's a saved property
                type_data[prop_type]['saved'] += 1
        
        return sorted(
            [{'type': k, **v} for k, v in type_data.items()],
            key=lambda x: x['inquiries'] + x['saved'],
            reverse=True
        )
    
    def _analyze_budget_preferences(self, user):
        """Analyze customer's budget preferences based on viewed/saved properties"""
        saved_properties = SavedProperty.objects.filter(customer=user).select_related('property')
        inquiries = Inquiry.objects.filter(customer=user).select_related('property')
        
        all_prices = []
        for item in list(saved_properties) + list(inquiries):
            property_obj = item.property if hasattr(item, 'property') else item.property
            if property_obj.price:
                all_prices.append(property_obj.price)
        
        if not all_prices:
            return {'min': 0, 'avg': 0, 'max': 0, 'range': 'No data'}
        
        min_price = min(all_prices)
        max_price = max(all_prices)
        avg_price = sum(all_prices) / len(all_prices)
        
        return {
            'min': min_price,
            'avg': round(avg_price, 2),
            'max': max_price,
            'range': f"{min_price:,.0f} - {max_price:,.0f}",
            'total_properties_analyzed': len(all_prices),
        }
    
    def _create_activity_timeline(self, user):
        """Create a timeline of customer activities"""
        activities = []
        
        # Add inquiries
        for inquiry in Inquiry.objects.filter(customer=user).select_related('property').order_by('-created_at')[:10]:
            activities.append({
                'type': 'inquiry',
                'title': f"Inquired about {inquiry.property.title}",
                'description': f"Status: {inquiry.status}",
                'date': inquiry.created_at,
                'property': inquiry.property,
            })
        
        # Add saved properties
        for saved in SavedProperty.objects.filter(customer=user).select_related('property').order_by('-saved_at')[:10]:
            activities.append({
                'type': 'saved',
                'title': f"Saved {saved.property.title}",
                'description': f"Property in {saved.property.location}",
                'date': saved.saved_at,
                'property': saved.property,
            })
        
        # Add viewings
        for viewing in PropertyViewing.objects.filter(customer=user).select_related('property').order_by('-scheduled_date')[:10]:
            activities.append({
                'type': 'viewing',
                'title': f"Property Viewing: {viewing.property.title}",
                'description': f"Status: {viewing.status}, Date: {viewing.scheduled_date}",
                'date': viewing.scheduled_date,
                'property': viewing.property,
            })
        
        # Sort by date and return recent activities
        return sorted(activities, key=lambda x: x['date'], reverse=True)[:8]
    
    def _get_recommended_properties(self, user):
        """Get recommended properties based on customer preferences"""
        # Analyze customer preferences
        saved_properties = SavedProperty.objects.filter(customer=user).select_related('property')
        
        if not saved_properties:
            # No preferences yet, show featured properties
            return Property.objects.filter(
                is_featured=True, is_active=True
            ).values('id', 'title', 'price', 'location', 'property_type', 'area_sqft')[:4]
        
        # Get preferred locations and types
        preferred_locations = list(
            saved_properties.values_list('property__location', flat=True)
            .annotate(count=Count('id'))
            .order_by('-count')[:3]
        )
        
        preferred_types = list(
            saved_properties.values_list('property__property_type', flat=True)
            .annotate(count=Count('id'))
            .order_by('-count')[:2]
        )
        
        # Get average budget
        avg_price = saved_properties.aggregate(
            avg_price=Avg('property__price')
        )['avg_price'] or 0
        
        # Find properties matching preferences (excluding already saved)
        recommended = Property.objects.filter(
            is_active=True,
            location__in=preferred_locations,
            property_type__in=preferred_types,
            price__lte=float(avg_price) * 1.2 if avg_price else 0  # Allow 20% above average
        ).exclude(
            id__in=saved_properties.values_list('property_id', flat=True)
        ).values('id', 'title', 'price', 'location', 'property_type', 'area_sqft')[:4]
        
        return recommended


class CustomerProfileView(CustomerDashboardMixin, TemplateView):
    """Customer profile management view with strict access control"""
    template_name = 'customer/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        profile, created = CustomerProfile.objects.get_or_create(user=user)
        context['profile'] = profile
        context['created'] = created
        
        return context


class CustomerInquiriesView(CustomerDashboardMixin, TemplateView):
    """Customer inquiries management view with strict access control"""
    template_name = 'customer/inquiries.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['inquiries'] = Inquiry.objects.filter(
            customer=user
        ).select_related('property').order_by('-created_at')
        
        return context


class CustomerSavedPropertiesView(CustomerDashboardMixin, TemplateView):
    """Customer saved properties view with strict access control"""
    template_name = 'customer/saved_properties.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['saved_properties'] = SavedProperty.objects.filter(
            customer=user
        ).select_related('property').order_by('-saved_at')
        
        return context


class CustomerViewingsView(CustomerDashboardMixin, TemplateView):
    """Customer property viewings view with strict access control"""
    template_name = 'customer/viewings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['viewings'] = PropertyViewing.objects.filter(
            customer=user
        ).select_related('property').order_by('-scheduled_date')

        return context


@require_POST
def update_profile(request):
    """Handle profile update via POST request"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    try:
        profile, created = CustomerProfile.objects.get_or_create(user=request.user)

        # Handle field-specific updates
        field = request.POST.get('field')
        value = request.POST.get('value')

        if field and value:
            # Handle single field update
            if field == 'full_name':
                name_parts = value.split(' ', 1)
                request.user.first_name = name_parts[0] if len(name_parts) > 0 else ''
                request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                request.user.save()
            elif field == 'phone':
                profile.phone = value
            elif field == 'contact_method':
                profile.preferred_contact_method = value
            profile.save()
            return JsonResponse({'success': True, 'message': 'Field updated successfully'})

        # Update user fields
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        if first_name:
            request.user.first_name = first_name
        if last_name:
            request.user.last_name = last_name
        request.user.save()

        # Update profile fields
        phone = request.POST.get('phone')
        preferred_contact_method = request.POST.get('preferred_contact_method')

        if phone:
            profile.phone = phone
        if preferred_contact_method:
            profile.preferred_contact_method = preferred_contact_method

        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()

        return JsonResponse({'success': True, 'message': 'Profile updated successfully'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def change_password(request):
    """Handle password change via POST request"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

    try:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            return JsonResponse({'success': False, 'error': 'Current password is incorrect'}, status=400)

        if new_password != confirm_password:
            return JsonResponse({'success': False, 'error': 'New passwords do not match'}, status=400)

        if len(new_password) < 8:
            return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters'}, status=400)

        request.user.set_password(new_password)
        request.user.save()

        return JsonResponse({'success': True, 'message': 'Password changed successfully'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
