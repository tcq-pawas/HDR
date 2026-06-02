from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.utils.text import slugify

from Apps.PublicPage.models import Property, PropertyImage
from .models import AgentProfile, PropertyInquiry
from .forms import PropertyForm, PropertyImageForm, AgentProfileForm


@login_required
def dashboard(request):
    """Agent/Seller Dashboard - Overview"""
    try:
        agent_profile = request.user.agent_profile
    except AgentProfile.DoesNotExist:
        agent_profile = AgentProfile.objects.create(user=request.user)
    
    # Get user's properties
    properties = Property.objects.filter(seller=request.user)
    
    # Dashboard statistics
    stats = {
        'total_properties': properties.count(),
        'active_properties': properties.filter(is_active=True).count(),
        'pending_approval': properties.filter(status='pending').count(),
        'approved_properties': properties.filter(status='approved').count(),
        'sold_properties': properties.filter(status='sold').count(),
        'total_inquiries': PropertyInquiry.objects.filter(
            property__seller=request.user
        ).count(),
        'unread_inquiries': PropertyInquiry.objects.filter(
            property__seller=request.user,
            is_read=False
        ).count(),
    }
    
    # Recent properties
    recent_properties = properties.order_by('-created_at')[:5]
    
    # Recent inquiries
    recent_inquiries = PropertyInquiry.objects.filter(
        property__seller=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'agent_profile': agent_profile,
        'stats': stats,
        'recent_properties': recent_properties,
        'recent_inquiries': recent_inquiries,
    }
    
    return render(request, 'agent/dashboard.html', context)


@login_required
def property_list(request):
    """List all properties created by the agent"""
    properties = Property.objects.filter(seller=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        properties = properties.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(properties, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'properties': page_obj.object_list,
        'status_filter': status_filter,
    }
    
    return render(request, 'agent/property_list.html', context)


@login_required
def property_add(request):
    """Add a new property"""
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.seller = request.user
            property_obj.status = 'pending'
            
            if not property_obj.slug:
                property_obj.slug = slugify(property_obj.title)
            
            property_obj.save()
            messages.success(request, "Property created successfully! It's pending admin approval.")
            return redirect('agent:property_edit', pk=property_obj.id)
    else:
        form = PropertyForm()
    
    context = {
        'form': form,
        'title': 'Add New Property'
    }
    
    return render(request, 'agent/property_form.html', context)


@login_required
def property_edit(request, pk):
    """Edit an existing property"""
    property_obj = get_object_or_404(Property, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully!")
            return redirect('agent:property_list')
    else:
        form = PropertyForm(instance=property_obj)
    
    # Get property images
    images = property_obj.images.all()
    image_form = PropertyImageForm()
    
    context = {
        'form': form,
        'property': property_obj,
        'images': images,
        'image_form': image_form,
        'title': f'Edit Property - {property_obj.title}'
    }
    
    return render(request, 'agent/property_edit.html', context)


@login_required
def property_delete(request, pk):
    """Delete a property"""
    property_obj = get_object_or_404(Property, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        property_title = property_obj.title
        property_obj.delete()
        messages.success(request, f"Property '{property_title}' deleted successfully!")
        return redirect('agent:property_list')
    
    context = {
        'property': property_obj
    }
    
    return render(request, 'agent/property_confirm_delete.html', context)


@login_required
def upload_property_image(request, pk):
    """Upload images for a property"""
    property_obj = get_object_or_404(Property, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        form = PropertyImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.property = property_obj
            image.save()
            messages.success(request, "Image uploaded successfully!")
            return redirect('agent:property_edit', pk=pk)
    else:
        form = PropertyImageForm()
    
    context = {
        'form': form,
        'property': property_obj,
    }
    
    return render(request, 'agent/image_upload.html', context)


@login_required
@require_http_methods(["POST"])
def delete_property_image(request, image_id):
    """Delete a property image"""
    image = get_object_or_404(PropertyImage, id=image_id, property__seller=request.user)
    property_id = image.property.id
    image.delete()
    messages.success(request, "Image deleted successfully!")
    return redirect('agent:property_edit', pk=property_id)


@login_required
def property_inquiries(request):
    """View inquiries for all agent's properties"""
    inquiries = PropertyInquiry.objects.filter(
        property__seller=request.user
    ).select_related('property').order_by('-created_at')
    
    # Mark as read
    PropertyInquiry.objects.filter(
        property__seller=request.user,
        is_read=False
    ).update(is_read=True)
    
    # Pagination
    paginator = Paginator(inquiries, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'inquiries': page_obj.object_list,
    }
    
    return render(request, 'agent/inquiries.html', context)


@login_required
def profile(request):
    """Agent profile management"""
    agent_profile, created = AgentProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = AgentProfileForm(request.POST, request.FILES, instance=agent_profile, user=request.user)
        if form.is_valid():
            # Update user info
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            
            # Save profile
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('agent:dashboard')
    else:
        form = AgentProfileForm(instance=agent_profile, user=request.user)
    
    context = {
        'form': form,
        'agent_profile': agent_profile,
    }
    
    return render(request, 'agent/profile.html', context)
