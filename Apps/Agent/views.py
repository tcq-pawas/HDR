from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Q, Count, Sum
from django.utils.text import slugify
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
import csv

from Apps.PublicPage.models import Property
from Apps.Administration.auth_utils import get_user_role
from .models import (
    AgentProfile, Lead, LeadFollowUp, SiteVisit,
    Booking, Installment, Commission, Document, Communication, MessageTemplate
)
from .forms import (
    PropertyForm, AgriculturalLandForm, AgentProfileForm, LeadForm,
    LeadFollowUpForm, SiteVisitForm, BookingForm, InstallmentForm,
    CommissionForm, DocumentForm, CommunicationForm, MessageTemplateForm
)


@login_required
def dashboard(request):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    """Agent/Seller Dashboard - Enhanced Overview"""
    try:
        agent_profile = request.user.agent_profile
    except AgentProfile.DoesNotExist:
        agent_profile = AgentProfile.objects.create(user=request.user)
    
    # Get user's properties
    properties = Property.objects.filter(seller=request.user)
    
    # Get today's date for filtering
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Enhanced dashboard statistics
    stats = {
        'total_properties': properties.count(),
        'active_properties': properties.filter(is_active=True).count(),
        'pending_approval': properties.filter(status='pending').count(),
        'approved_properties': properties.filter(status='approved').count(),
        'sold_properties': properties.filter(status='sold').count(),
        # New CRM metrics
        'total_leads': Lead.objects.filter(agent=request.user).count(),
        'new_leads_today': Lead.objects.filter(
            agent=request.user,
            created_at__date=today
        ).count(),
        'scheduled_visits': SiteVisit.objects.filter(
            agent=request.user,
            scheduled_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).count(),
        'bookings_this_month': Booking.objects.filter(
            agent=request.user,
            booking_date__month=today.month,
            booking_date__year=today.year
        ).count(),
        'total_sales': Booking.objects.filter(
            agent=request.user,
            status='payment_completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'commission_earned': Commission.objects.filter(
            agent=request.user,
            status='paid'
        ).aggregate(total=Sum('commission_amount'))['total'] or 0,
        'pending_commission': Commission.objects.filter(
            agent=request.user,
            status__in=['pending', 'approved']
        ).aggregate(total=Sum('commission_amount'))['total'] or 0,
    }
    
    # Recent properties
    recent_properties = properties.select_related('seller').order_by('-created_at')[:5]
    
    # Recent leads
    recent_leads = Lead.objects.filter(agent=request.user).select_related('property').order_by('-created_at')[:5]
    
    # Upcoming site visits
    upcoming_visits = SiteVisit.objects.filter(
        agent=request.user,
        scheduled_date__gte=today,
        status__in=['scheduled', 'confirmed']
    ).select_related('property', 'lead').order_by('scheduled_date')[:5]
    
    # Recent bookings
    recent_bookings = Booking.objects.filter(agent=request.user).select_related('property', 'lead').order_by('-booking_date')[:5]
    
    context = {
        'agent_profile': agent_profile,
        'stats': stats,
        'recent_properties': recent_properties,
        'recent_leads': recent_leads,
        'upcoming_visits': upcoming_visits,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'agent/dashboard.html', context)


@login_required
def property_list(request):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    """List all properties created by the agent"""
    properties = Property.objects.filter(seller=request.user).select_related('seller').order_by('-created_at')
    
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
def property_type_select(request):
    """Select property type before adding"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    return render(request, 'agent/property_type_select.html')


@login_required
def property_add(request, property_type):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    """Add a new property"""
    if request.method == 'POST':
        # Use AgriculturalLandForm for land properties
        if property_type == 'land':
            form = AgriculturalLandForm(request.POST, request.FILES)
        else:
            form = PropertyForm(request.POST, request.FILES)
        
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.seller = request.user
            property_obj.status = 'pending'
            property_obj.created_by = request.user
            property_obj.last_updated_by = request.user
            
            # Set property type and category based on selection
            if property_type == 'land':
                property_obj.property_type = 'sale'
                property_obj.category = 'Plots'
            elif property_type == 'house':
                property_obj.property_type = 'sale'
                property_obj.category = 'Apartments'
            
            if not property_obj.slug:
                property_obj.slug = slugify(property_obj.title)
            
            property_obj.save()
            messages.success(request, "Property created successfully! It's pending admin approval.")
            return redirect('agent:property_edit', pk=property_obj.id)
    else:
        # Use appropriate form based on property_type
        if property_type == 'land':
            form = AgriculturalLandForm()
        else:
            initial_category = 'Apartments' if property_type == 'house' else 'Plots'
            form = PropertyForm(initial={'property_type': 'sale', 'category': initial_category})
    
    context = {
        'form': form,
        'property_type': property_type,
        'title': f'Add {property_type.title()}'
    }
    
    # Use different template for agricultural land
    if property_type == 'land':
        return render(request, 'agent/agricultural_land_form.html', context)
    else:
        return render(request, 'agent/property_form.html', context)


@login_required
def property_edit(request, pk):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    """Edit an existing property"""
    property_obj = get_object_or_404(Property.objects.select_related('seller'), pk=pk, seller=request.user)
    
    # Determine property_type from category for field visibility
    if property_obj.category == 'Plots':
        property_type = 'land'
    else:
        property_type = 'house'
    
    if request.method == 'POST':
        # Use AgriculturalLandForm for land properties
        if property_type == 'land':
            form = AgriculturalLandForm(request.POST, request.FILES, instance=property_obj)
        else:
            form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.last_updated_by = request.user
            property_obj.save()
            messages.success(request, "Property updated successfully!")
            return redirect('agent:property_list')
    else:
        # Use appropriate form based on property_type
        if property_type == 'land':
            form = AgriculturalLandForm(instance=property_obj)
        else:
            form = PropertyForm(instance=property_obj)
    
    # Get property images
    images = property_obj.images.all()
    
    context = {
        'form': form,
        'property': property_obj,
        'images': images,
        'property_type': property_type,
        'title': f'Edit Property - {property_obj.title}'
    }
    
    # Use different template for agricultural land
    if property_type == 'land':
        return render(request, 'agent/agricultural_land_form.html', context)
    else:
        return render(request, 'agent/property_form.html', context)


@login_required
def property_delete(request, pk):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    """Delete a property"""
    property_obj = get_object_or_404(Property.objects.select_related('seller'), pk=pk, seller=request.user)
    
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
def settings(request):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    """Settings page"""
    try:
        agent_profile = request.user.agent_profile
    except AgentProfile.DoesNotExist:
        agent_profile = AgentProfile.objects.create(user=request.user)
    
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
            messages.success(request, "Settings updated successfully!")
            return redirect('agent:settings')
    else:
        form = AgentProfileForm(instance=agent_profile, user=request.user)
    
    context = {
        'form': form,
        'agent_profile': agent_profile,
    }
    
    return render(request, 'agent/settings.html', context)


@login_required
def lead_list(request):
    """List all leads for the agent"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    leads = Lead.objects.filter(agent=request.user).select_related('property').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    # Filter by source
    source_filter = request.GET.get('source')
    if source_filter:
        leads = leads.filter(source=source_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(leads, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'leads': page_obj.object_list,
        'status_filter': status_filter,
        'source_filter': source_filter,
    }
    
    return render(request, 'agent/lead_list.html', context)


@login_required
def lead_add(request):
    """Add a new lead"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.agent = request.user
            lead.save()
            messages.success(request, "Lead created successfully!")
            return redirect('agent:lead_detail', pk=lead.id)
    else:
        form = LeadForm()
    
    # Filter properties to only show agent's properties
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    
    context = {
        'form': form,
        'title': 'Add New Lead'
    }
    
    return render(request, 'agent/lead_form.html', context)


@login_required
def lead_detail(request, pk):
    """View lead details"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    lead = get_object_or_404(Lead.objects.select_related('property', 'agent'), pk=pk, agent=request.user)
    follow_ups = lead.follow_ups.all().order_by('-scheduled_date')
    
    context = {
        'lead': lead,
        'follow_ups': follow_ups,
    }
    
    return render(request, 'agent/lead_detail.html', context)


@login_required
def lead_edit(request, pk):
    """Edit a lead"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    lead = get_object_or_404(Lead.objects.select_related('property', 'agent'), pk=pk, agent=request.user)
    
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, "Lead updated successfully!")
            return redirect('agent:lead_detail', pk=lead.id)
    else:
        form = LeadForm(instance=lead)
    
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    
    context = {
        'form': form,
        'lead': lead,
        'title': f'Edit Lead - {lead.name}'
    }
    
    return render(request, 'agent/lead_form.html', context)


@login_required
def lead_add_followup(request, pk):
    """Add a follow-up to a lead"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    lead = get_object_or_404(Lead.objects.select_related('agent'), pk=pk, agent=request.user)
    
    if request.method == 'POST':
        form = LeadFollowUpForm(request.POST)
        if form.is_valid():
            follow_up = form.save(commit=False)
            follow_up.lead = lead
            follow_up.agent = request.user
            follow_up.save()
            messages.success(request, "Follow-up added successfully!")
            return redirect('agent:lead_detail', pk=lead.id)
    else:
        form = LeadFollowUpForm()
    
    context = {
        'form': form,
        'lead': lead,
        'title': f'Add Follow-up for {lead.name}'
    }
    
    return render(request, 'agent/lead_followup_form.html', context)


@login_required
def site_visit_list(request):
    """List all site visits for the agent"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    visits = SiteVisit.objects.filter(agent=request.user).select_related('property', 'lead').order_by('-scheduled_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        visits = visits.filter(status=status_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        visits = visits.filter(scheduled_date__date__gte=date_from)
    if date_to:
        visits = visits.filter(scheduled_date__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(visits, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'visits': page_obj.object_list,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'agent/site_visit_list.html', context)


@login_required
def site_visit_add(request):
    """Schedule a new site visit"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = SiteVisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.agent = request.user
            visit.save()
            messages.success(request, "Site visit scheduled successfully!")
            return redirect('agent:site_visit_list')
    else:
        form = SiteVisitForm()
    
    # Filter properties and leads to only show agent's data
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    form.fields['lead'].queryset = Lead.objects.filter(agent=request.user)
    
    context = {
        'form': form,
        'title': 'Schedule Site Visit'
    }
    
    return render(request, 'agent/site_visit_form.html', context)


@login_required
def site_visit_detail(request, pk):
    """View site visit details"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    visit = get_object_or_404(SiteVisit.objects.select_related('property', 'lead', 'agent'), pk=pk, agent=request.user)
    
    if request.method == 'POST':
        # Update visit status and feedback
        visit.status = request.POST.get('status', visit.status)
        visit.feedback = request.POST.get('feedback', '')
        visit.save()
        messages.success(request, "Site visit updated successfully!")
        return redirect('agent:site_visit_detail', pk=pk)
    
    context = {
        'visit': visit,
    }
    
    return render(request, 'agent/site_visit_detail.html', context)


@login_required
def site_visit_edit(request, pk):
    """Edit a site visit"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    visit = get_object_or_404(SiteVisit.objects.select_related('property', 'lead', 'agent'), pk=pk, agent=request.user)
    
    if request.method == 'POST':
        form = SiteVisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, "Site visit updated successfully!")
            return redirect('agent:site_visit_detail', pk=pk)
    else:
        form = SiteVisitForm(instance=visit)
    
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    form.fields['lead'].queryset = Lead.objects.filter(agent=request.user)
    
    context = {
        'form': form,
        'visit': visit,
        'title': f'Edit Site Visit'
    }
    
    return render(request, 'agent/site_visit_form.html', context)


@login_required
def booking_list(request):
    """List all bookings for the agent"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    bookings = Booking.objects.filter(agent=request.user).select_related('property', 'lead').order_by('-booking_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'status_filter': status_filter,
    }
    
    return render(request, 'agent/booking_list.html', context)


@login_required
def booking_add(request):
    """Create a new booking"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.agent = request.user
            booking.save()
            messages.success(request, "Booking created successfully!")
            return redirect('agent:booking_detail', pk=booking.id)
    else:
        form = BookingForm()
    
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    form.fields['lead'].queryset = Lead.objects.filter(agent=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Booking'
    }
    
    return render(request, 'agent/booking_form.html', context)


@login_required
def booking_detail(request, pk):
    """View booking details"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    booking = get_object_or_404(Booking.objects.select_related('property', 'lead', 'agent').prefetch_related('installments'), pk=pk, agent=request.user)
    installments = booking.installments.all().order_by('installment_number')
    
    context = {
        'booking': booking,
        'installments': installments,
    }
    
    return render(request, 'agent/booking_detail.html', context)


@login_required
def booking_edit(request, pk):
    """Edit a booking"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    booking = get_object_or_404(Booking.objects.select_related('property', 'lead', 'agent'), pk=pk, agent=request.user)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, "Booking updated successfully!")
            return redirect('agent:booking_detail', pk=pk)
    else:
        form = BookingForm(instance=booking)
    
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    form.fields['lead'].queryset = Lead.objects.filter(agent=request.user)
    
    context = {
        'form': form,
        'booking': booking,
        'title': f'Edit Booking'
    }
    
    return render(request, 'agent/booking_form.html', context)


@login_required
def installment_add(request, booking_pk):
    """Add an installment to a booking"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    booking = get_object_or_404(Booking.objects.select_related('agent'), pk=booking_pk, agent=request.user)
    
    if request.method == 'POST':
        form = InstallmentForm(request.POST)
        if form.is_valid():
            installment = form.save(commit=False)
            installment.booking = booking
            installment.save()
            messages.success(request, "Installment added successfully!")
            return redirect('agent:booking_detail', pk=booking.id)
    else:
        form = InstallmentForm()
    
    context = {
        'form': form,
        'booking': booking,
        'title': f'Add Installment for Booking'
    }
    
    return render(request, 'agent/installment_form.html', context)


@login_required
def installment_edit(request, pk):
    """Edit an installment"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    installment = get_object_or_404(Installment.objects.select_related('booking__agent'), pk=pk, booking__agent=request.user)
    
    if request.method == 'POST':
        form = InstallmentForm(request.POST, instance=installment)
        if form.is_valid():
            form.save()
            messages.success(request, "Installment updated successfully!")
            return redirect('agent:booking_detail', pk=installment.booking.id)
    else:
        form = InstallmentForm(instance=installment)
    
    context = {
        'form': form,
        'installment': installment,
        'title': f'Edit Installment'
    }
    
    return render(request, 'agent/installment_form.html', context)


@login_required
def commission_list(request):
    """List all commissions for the agent"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    commissions = Commission.objects.filter(agent=request.user).select_related('booking', 'property').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        commissions = commissions.filter(status=status_filter)
    
    # Calculate totals
    total_earned = commissions.filter(status='paid').aggregate(total=Sum('commission_amount'))['total'] or 0
    total_pending = commissions.filter(status__in=['pending', 'approved']).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    # Pagination
    paginator = Paginator(commissions, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'commissions': page_obj.object_list,
        'status_filter': status_filter,
        'total_earned': total_earned,
        'total_pending': total_pending,
    }
    
    return render(request, 'agent/commission_list.html', context)


@login_required
def commission_detail(request, pk):
    """View commission details"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    commission = get_object_or_404(Commission.objects.select_related('property', 'booking', 'agent'), pk=pk, agent=request.user)
    
    context = {
        'commission': commission,
    }
    
    return render(request, 'agent/commission_detail.html', context)


@login_required
def document_list(request):
    """List all documents for the agent"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    documents = Document.objects.filter(agent=request.user).select_related('property', 'booking').order_by('-uploaded_at')
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        documents = documents.filter(document_type=type_filter)
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        documents = documents.filter(category=category_filter)
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'documents': page_obj.object_list,
        'type_filter': type_filter,
        'category_filter': category_filter,
    }
    
    return render(request, 'agent/document_list.html', context)


@login_required
def document_add(request):
    """Upload a new document"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.agent = request.user
            document.file_size = request.FILES['file'].size
            document.save()
            messages.success(request, "Document uploaded successfully!")
            return redirect('agent:document_list')
    else:
        form = DocumentForm()
    
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    form.fields['booking'].queryset = Booking.objects.filter(agent=request.user)
    
    context = {
        'form': form,
        'title': 'Upload Document'
    }
    
    return render(request, 'agent/document_form.html', context)


@login_required
def document_delete(request, pk):
    """Delete a document"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    document = get_object_or_404(Document.objects.select_related('agent'), pk=pk, agent=request.user)
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, "Document deleted successfully!")
        return redirect('agent:document_list')
    
    context = {
        'document': document,
    }
    
    return render(request, 'agent/document_confirm_delete.html', context)


@login_required
def communication_list(request):
    """List all communications for the agent"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    communications = Communication.objects.filter(agent=request.user).select_related('lead', 'booking').order_by('-sent_at')
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        communications = communications.filter(communication_type=type_filter)
    
    # Pagination
    paginator = Paginator(communications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'communications': page_obj.object_list,
        'type_filter': type_filter,
    }
    
    return render(request, 'agent/communication_list.html', context)


@login_required
def communication_send(request):
    """Send a new communication"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = CommunicationForm(request.POST)
        if form.is_valid():
            communication = form.save(commit=False)
            communication.agent = request.user
            communication.save()
            messages.success(request, "Communication sent successfully!")
            return redirect('agent:communication_list')
    else:
        form = CommunicationForm()
    
    # Filter templates to only show agent's templates
    form.fields['template_used'].queryset = MessageTemplate.objects.filter(agent=request.user, is_active=True)
    
    context = {
        'form': form,
        'title': 'Send Communication'
    }
    
    return render(request, 'agent/communication_form.html', context)


@login_required
def message_template_list(request):
    """List all message templates for the agent"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    templates = MessageTemplate.objects.filter(agent=request.user).order_by('name')
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'agent/message_template_list.html', context)


@login_required
def message_template_add(request):
    """Create a new message template"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.agent = request.user
            template.save()
            messages.success(request, "Template created successfully!")
            return redirect('agent:message_template_list')
    else:
        form = MessageTemplateForm()
    
    context = {
        'form': form,
        'title': 'Create Message Template'
    }
    
    return render(request, 'agent/message_template_form.html', context)


@login_required
def message_template_edit(request, pk):
    """Edit a message template"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    template = get_object_or_404(MessageTemplate.objects.select_related('agent'), pk=pk, agent=request.user)
    
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Template updated successfully!")
            return redirect('agent:message_template_list')
    else:
        form = MessageTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': f'Edit Template'
    }
    
    return render(request, 'agent/message_template_form.html', context)


# ==================== Customer Management Views ====================

@login_required
def customer_list(request):
    """List all customers (from bookings and leads)"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    # Get unique customers from bookings and leads
    bookings = Booking.objects.filter(agent=request.user).values('customer_name', 'customer_phone', 'customer_email').distinct()
    leads = Lead.objects.filter(agent=request.user).values('name', 'phone', 'email').distinct()
    
    # Combine and deduplicate
    customers = []
    seen = set()
    
    for booking in bookings:
        key = (booking['customer_phone'],)
        if key not in seen:
            customers.append({
                'name': booking['customer_name'],
                'phone': booking['customer_phone'],
                'email': booking['customer_email'],
                'source': 'Booking',
            })
            seen.add(key)
    
    for lead in leads:
        key = (lead['phone'],)
        if key not in seen:
            customers.append({
                'name': lead['name'],
                'phone': lead['phone'],
                'email': lead['email'],
                'source': 'Lead',
            })
            seen.add(key)
    
    context = {
        'customers': customers,
    }
    
    return render(request, 'agent/customer_list.html', context)


@login_required
def customer_detail(request, phone):
    """View customer details"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    # Get customer's bookings
    bookings = Booking.objects.filter(agent=request.user, customer_phone=phone).select_related('property')
    
    # Get customer's leads
    leads = Lead.objects.filter(agent=request.user, phone=phone).select_related('property')
    
    # Get customer's site visits
    visits = SiteVisit.objects.filter(agent=request.user, customer_phone=phone).select_related('property')
    
    # Get customer's communications
    communications = Communication.objects.filter(agent=request.user, recipient=phone)
    
    context = {
        'phone': phone,
        'bookings': bookings,
        'leads': leads,
        'visits': visits,
        'communications': communications,
    }
    
    return render(request, 'agent/customer_detail.html', context)


@login_required
def reports(request):
    """Enhanced reports and analytics page"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    # Get date range from request
    date_range = request.GET.get('range', '30')
    days = int(date_range)
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Sales data
    sales_data = Booking.objects.filter(
        agent=request.user,
        booking_date__gte=start_date
    ).values('booking_date__date').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('booking_date__date')
    
    # Lead conversion data
    leads_data = Lead.objects.filter(
        agent=request.user,
        created_at__gte=start_date
    ).values('status').annotate(count=Count('id'))
    
    # Property performance
    property_data = Property.objects.filter(
        seller=request.user
    ).annotate(
        leads_count=Count('leads'),
        views_count=Count('inquiries')
    ).order_by('-leads_count')[:10]
    
    # Commission data
    commission_data = Commission.objects.filter(
        agent=request.user,
        created_at__gte=start_date
    ).values('status').annotate(total=Sum('commission_amount'))
    
    context = {
        'date_range': date_range,
        'sales_data': list(sales_data),
        'leads_data': list(leads_data),
        'property_data': property_data,
        'commission_data': list(commission_data),
    }
    
    return render(request, 'agent/reports.html', context)


@login_required
def export_report(request, report_type):
    """Export reports to CSV"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'leads':
        writer.writerow(['Name', 'Email', 'Phone', 'Status', 'Source', 'Budget', 'Created Date'])
        leads = Lead.objects.filter(agent=request.user)
        for lead in leads:
            writer.writerow([lead.name, lead.email, lead.phone, lead.status, lead.source, lead.budget, lead.created_at])
    
    elif report_type == 'bookings':
        writer.writerow(['Customer Name', 'Property', 'Status', 'Total Amount', 'Booking Date'])
        bookings = Booking.objects.filter(agent=request.user)
        for booking in bookings:
            writer.writerow([booking.customer_name, booking.property.title, booking.status, booking.total_amount, booking.booking_date])
    
    elif report_type == 'commissions':
        writer.writerow(['Property', 'Commission Amount', 'Status', 'Due Date', 'Paid Date'])
        commissions = Commission.objects.filter(agent=request.user)
        for commission in commissions:
            writer.writerow([commission.property.title, commission.commission_amount, commission.status, commission.due_date, commission.paid_date])
    
    elif report_type == 'site_visits':
        writer.writerow(['Customer Name', 'Property', 'Scheduled Date', 'Status'])
        visits = SiteVisit.objects.filter(agent=request.user)
        for visit in visits:
            writer.writerow([visit.customer_name, visit.property.title, visit.scheduled_date, visit.status])
    
    return response
