from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from Apps.PublicPage.models import Property, PropertyImage
from .forms import PropertyForm

def sell_page(request):
    """Sell Page Landing - Shows info and guides users to login or dashboard"""
    return render(request, 'sell/sell_page.html')

@login_required
def property_list(request):
    """List properties owned by the logged-in seller"""
    properties = Property.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'sell/property_list.html', {'properties': properties})

@login_required
def property_detail(request, pk):
    """Detailed view of a property owned by the seller"""
    property_obj = get_object_or_404(Property, pk=pk)
    if property_obj.seller != request.user and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to view this property.")
    
    return render(request, 'sell/property_detail.html', {
        'property': property_obj,
        'images': property_obj.images.all()
    })

@login_required
def property_create(request):
    """Create a new property listing with seller assignment and multiple image uploads"""
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.seller = request.user
            property_obj.status = 'pending'  # New properties default to Pending
            property_obj.save()
            
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for img in images:
                PropertyImage.objects.create(property=property_obj, image=img)
                
            messages.success(request, "Property created successfully and is pending approval.")
            return redirect('sell:property_list')
    else:
        form = PropertyForm()
        
    return render(request, 'sell/property_form.html', {
        'form': form,
        'title': 'Create Property Listing',
        'is_create': True
    })

@login_required
def property_update(request, pk):
    """Update an existing property listing and allow adding more images"""
    property_obj = get_object_or_404(Property, pk=pk)
    if property_obj.seller != request.user and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to edit this property.")
        
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            property_obj = form.save()
            
            # Add optional new images
            images = request.FILES.getlist('images')
            for img in images:
                PropertyImage.objects.create(property=property_obj, image=img)
                
            messages.success(request, "Property listing updated successfully.")
            return redirect('sell:property_list')
    else:
        form = PropertyForm(instance=property_obj)
        
    return render(request, 'sell/property_form.html', {
        'form': form,
        'property': property_obj,
        'title': 'Edit Property Listing',
        'is_create': False
    })

@login_required
def property_delete(request, pk):
    """Delete a seller property listing"""
    property_obj = get_object_or_404(Property, pk=pk)
    if property_obj.seller != request.user and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to delete this property.")
        
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, "Property listing deleted successfully.")
        return redirect('sell:property_list')
        
    return render(request, 'sell/property_confirm_delete.html', {'property': property_obj})
