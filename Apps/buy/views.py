from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from Apps.PublicPage.models import Property, PropertyInquiry, LocationData
from Apps.Customer.models import SavedProperty
from .forms import InquiryForm
from Apps.Agent.models import Lead, LeadFollowUp
from django.utils import timezone
from django.views.decorators.http import require_POST

def property_search(request):
    """Browse and search active and approved property listings with map integration"""
    # Show only active, approved properties
    properties = Property.objects.filter(
        is_active=True, 
        status='approved',
        show_to_public=True,
        is_admin_list=False
    ).prefetch_related('images').order_by('-created_at')
    
    # Extract search filters
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    price_range = request.GET.get('price_range', '')
    property_type = request.GET.get('property_type', '')
    area_range = request.GET.get('area_range', '')
    area_unit = request.GET.get('area_unit', 'Sq Ft')
    status_filter = request.GET.get('status', '')
    sale_by = request.GET.get('sale_by', '')
    sort_by = request.GET.get('sort_by', '-created_at')
    
    # Apply filters
    if query:
        properties = properties.filter(
            Q(title__icontains=query) | 
            Q(public_description__icontains=query) |
            Q(location__icontains=query)
        )
    
    if location:
        properties = properties.filter(location__icontains=location)
    
    if price_range:
        # Price range filtering
        price_filters = {
            'under_10_lac': (0, 1000000),
            '10_50_lac': (1000000, 5000000),
            '50_lac_1cr': (5000000, 10000000),
            '1cr_10cr': (10000000, 100000000),
            'above_10cr': (100000000, float('inf'))
        }
        if price_range in price_filters:
            min_p, max_p = price_filters[price_range]
            properties = properties.filter(price__gte=min_p, price__lte=max_p)
    
    if property_type:
        properties = properties.filter(category=property_type)
    
    if area_range:
        # Area range filtering (placeholder - would need area field)
        pass
    
    # Apply sorting
    sort_options = {
        'latest': '-created_at',
        'price_low': 'price',
        'price_high': '-price',
        'area_low': 'area_sqft',
        'area_high': '-area_sqft'
    }
    if sort_by in sort_options:
        properties = properties.order_by(sort_options[sort_by])
    
    # Pagination
    paginator = Paginator(properties, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'properties': page_obj.object_list,
        'total_results': paginator.count,
        'property_types': ['Agricultural', 'Residential', 'Commercial', 'Farm Land', 'Plot'],
        'price_ranges': [
            ('Under ₹10 Lac', 'under_10_lac'),
            ('₹10 Lac - ₹50 Lac', '10_50_lac'),
            ('₹50 Lac - ₹1 Cr', '50_lac_1cr'),
            ('₹1 Cr - ₹10 Cr', '1cr_10cr'),
            ('Above ₹10 Cr', 'above_10cr'),
        ],
        'area_units': ['Acre', 'Bigha', 'Hectare', 'Sq Ft', 'Sq Yard'],
        'filters': {
            'q': query,
            'location': location,
            'price_range': price_range,
            'property_type': property_type,
            'area_range': area_range,
            'area_unit': area_unit,
            'status': status_filter,
            'sale_by': sale_by,
            'sort_by': sort_by,
        }
    }
    
    return render(request, 'buy/property_search.html', context)

def location_autocomplete(request):
    """Return location suggestions from LocationData when query has at least 3 letters."""
    query = request.GET.get('q', '').strip()
    alpha_count = sum(1 for c in query if c.isalpha())
    if alpha_count < 3:
        return JsonResponse({'results': []})

    locations = (
        LocationData.objects
        .filter(display_name__icontains=query)
        .values_list('display_name', flat=True)
        .distinct()[:15]
    )
    return JsonResponse({'results': list(locations)})

def property_detail(request, pk):
    """View details of a property listing and allow submitting an inquiry"""
    from Apps.Administration.auth_utils import get_user_role
    is_user_admin = False
    if request.user.is_authenticated:
        role = get_user_role(request.user)
        is_user_admin = (role == 'admin' or request.user.is_superuser or request.user.is_staff)
        
    kwargs = {'pk': pk, 'is_active': True, 'status': 'approved'}
    if not is_user_admin:
        kwargs['is_admin_list'] = False
        
    property_obj = get_object_or_404(Property, **kwargs)
    form = InquiryForm()
    
    # Check if this property is saved by current user
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedProperty.objects.filter(customer=request.user, property=property_obj).exists()
    
    # Get similar properties (same category, excluding current property)
    similar_properties = Property.objects.filter(
        is_active=True,
        status='approved',
        show_to_public=True,
        is_admin_list=False,
        category=property_obj.category
    ).exclude(pk=pk).prefetch_related('images')[:6]
        
    return render(request, 'buy/property_detail.html', {
        'property': property_obj,
        'images': property_obj.images.all(),
        'form': form,
        'is_saved': is_saved,
        'similar_properties': similar_properties
    })

@login_required
def saved_properties(request):
    """Display properties saved by the logged-in customer"""
    saved_items = SavedProperty.objects.filter(customer=request.user).select_related('property').order_by('-saved_at')
    return render(request, 'buy/saved_properties.html', {'saved_items': saved_items})

@login_required
@require_POST
def save_property(request, pk):
    """Save a property to the user's saved properties list"""
    from Apps.Administration.auth_utils import get_user_role
    is_user_admin = False
    if request.user.is_authenticated:
        role = get_user_role(request.user)
        is_user_admin = (role == 'admin' or request.user.is_superuser or request.user.is_staff)
        
    kwargs = {'pk': pk, 'is_active': True, 'status': 'approved'}
    if not is_user_admin:
        kwargs['is_admin_list'] = False
        
    property_obj = get_object_or_404(Property, **kwargs)
    SavedProperty.objects.get_or_create(customer=request.user, property=property_obj)
    messages.success(request, f'"{property_obj.title}" has been saved to your list.')
    return redirect('buy:property_detail', pk=pk)

@login_required
@require_POST
def remove_saved_property(request, pk):
    """Remove a property from the user's saved properties list"""
    property_obj = get_object_or_404(Property, pk=pk)
    SavedProperty.objects.filter(customer=request.user, property=property_obj).delete()
    messages.success(request, f'"{property_obj.title}" was removed from your saved properties.')
    
    # Redirect back to referring page or saved properties dashboard
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('buy:saved_properties')

def send_inquiry(request, pk):
    """Handle inquiry submission for a specific property listing"""
    from Apps.Administration.auth_utils import get_user_role
    is_user_admin = False
    if request.user.is_authenticated:
        role = get_user_role(request.user)
        is_user_admin = (role == 'admin' or request.user.is_superuser or request.user.is_staff)
        
    kwargs = {'pk': pk, 'is_active': True, 'status': 'approved'}
    if not is_user_admin:
        kwargs['is_admin_list'] = False
        
    property_obj = get_object_or_404(Property, **kwargs)
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.related_property = property_obj
            inquiry.phone_number = request.POST.get('phone')
            if property_obj.seller:
                agent_profile = getattr(property_obj.seller, 'agent_profile', None)
                inquiry.agent_profile = agent_profile
            inquiry.save()
            
            #Lead create + follow up note
            phone_value = getattr(inquiry, 'phone', None) or request.POST.get('phone')
            message_value = getattr(inquiry, 'message', None) or request.POST.get('message')
            
            if property_obj.seller and phone_value:
                lead, created = Lead.objects.get_or_create(
                    agent=property_obj.seller,
                    phone=phone_value,
                    defaults={
                        'name': getattr(inquiry, 'name', None) or 'Website Visitor',
                        'email': getattr(inquiry, 'email', None),
                        'property': property_obj,
                        'source': 'website',
                        'status': 'new',
                    }                   
                )
                
                if not created:
                    lead.property = property_obj
                    lead.save(update_fields=['property'])

                # Add message
                if message_value:
                    LeadFollowUp.objects.create(
                        lead=lead,
                        agent=property_obj.seller,
                        notes=f"Inquiry for '{property_obj.title}': {message_value}",
                        scheduled_date=timezone.now(),
                    )
            messages.success(request, "Your inquiry has been sent to the seller successfully!")
            return redirect('buy:property_detail', pk=pk)
            
    messages.error(request, "Failed to submit inquiry. Please check the form fields.")
    return redirect('buy:property_detail', pk=pk)


