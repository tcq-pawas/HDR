from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from Apps.PublicPage.models import Property, PropertyInquiry
from Apps.Customer.models import SavedProperty
from .forms import InquiryForm

def property_search(request):
    """Browse and search active and approved property listings with map integration"""
    # Show only active, approved properties
    properties = Property.objects.filter(
        is_active=True, 
        status='approved',
        show_to_public=True
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
    paginator = Paginator(properties, 12)
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

def property_detail(request, pk):
    """View details of a property listing and allow submitting an inquiry"""
    property_obj = get_object_or_404(Property, pk=pk, is_active=True, status='approved')
    form = InquiryForm()
    
    # Check if this property is saved by current user
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedProperty.objects.filter(customer=request.user, property=property_obj).exists()
        
    return render(request, 'buy/property_detail.html', {
        'property': property_obj,
        'images': property_obj.images.all(),
        'form': form,
        'is_saved': is_saved
    })

@login_required
def saved_properties(request):
    """Display properties saved by the logged-in customer"""
    saved_items = SavedProperty.objects.filter(customer=request.user).select_related('property').order_by('-saved_at')
    return render(request, 'buy/saved_properties.html', {'saved_items': saved_items})

@login_required
def save_property(request, pk):
    """Save a property to the user's saved properties list"""
    property_obj = get_object_or_404(Property, pk=pk, is_active=True, status='approved')
    SavedProperty.objects.get_or_create(customer=request.user, property=property_obj)
    messages.success(request, f'"{property_obj.title}" has been saved to your list.')
    return redirect('buy:property_detail', pk=pk)

@login_required
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
    property_obj = get_object_or_404(Property, pk=pk, is_active=True, status='approved')
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.property = property_obj
            inquiry.save()
            messages.success(request, "Your inquiry has been sent to the seller successfully!")
            return redirect('buy:property_detail', pk=pk)
            
    messages.error(request, "Failed to submit inquiry. Please check the form fields.")
    return redirect('buy:property_detail', pk=pk)
