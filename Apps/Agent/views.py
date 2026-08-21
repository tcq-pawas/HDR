from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse, Http404
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils.text import slugify
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
import csv

from django.views.decorators.http import require_GET
from Apps.PublicPage.models import Property, PropertyInquiry, LocationData, PropertyImage
from Apps.Administration.auth_utils import get_user_role
from Apps.Subscriptions.models import UserSubscription
from Apps.Subscriptions.utils import (
    SUBSCRIPTION_UNSET,
    check_property_listing_eligibility,
)
from .models import (
    AgentProfile, Lead, LeadFollowUp, SiteVisit,
    Booking, Installment, Commission, Document, VerificationDocument,
    Communication, MessageTemplate
)
from .validators import validate_image_file, validate_document_file, validate_video_file, ValidationError
from .forms import (
    PropertyForm, AgriculturalLandForm, AgentProfileForm, LeadForm,
    LeadFollowUpForm, SiteVisitForm, BookingForm, InstallmentForm,
    CommissionForm, DocumentForm, VerificationDocumentForm,
    CommunicationForm, MessageTemplateForm
)

from datetime import datetime, timedelta

MIN_ALLOWED_DATE = datetime(2020, 1, 1).date()
MAX_RANGE_DAYS = 365

def parse_safe_date(value):
    """Safely parses the date string received from the URL. If the date is invalid, it returns None instead of crashing."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def get_safe_date_range(request):
    """
    Leads jaise filters ke liye — future date allow NAHI karta.
    """
    today = timezone.now().date()

    date_from = parse_safe_date(request.GET.get('date_from'))
    date_to = parse_safe_date(request.GET.get('date_to'))

    if date_from and date_from < MIN_ALLOWED_DATE:
        date_from = MIN_ALLOWED_DATE
    if date_from and date_from > today:
        date_from = today

    if date_to and date_to > today:
        date_to = today
    if date_to and date_to < MIN_ALLOWED_DATE:
        date_to = MIN_ALLOWED_DATE

    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from

    if date_from and date_to and (date_to - date_from).days > MAX_RANGE_DAYS:
        date_from = date_to - timedelta(days=MAX_RANGE_DAYS)

    return date_from, date_to


def get_safe_date_range_with_future(request):
    """
    Site Visits jaise filters ke liye — future date allow karta hai (max 2 saal aage tak).
    """
    today = timezone.now().date()
    MAX_FUTURE_DATE = today + timedelta(days=730)

    date_from = parse_safe_date(request.GET.get('date_from'))
    date_to = parse_safe_date(request.GET.get('date_to'))

    if date_from and date_from < MIN_ALLOWED_DATE:
        date_from = MIN_ALLOWED_DATE
    if date_from and date_from > MAX_FUTURE_DATE:
        date_from = MAX_FUTURE_DATE

    if date_to and date_to < MIN_ALLOWED_DATE:
        date_to = MIN_ALLOWED_DATE
    if date_to and date_to > MAX_FUTURE_DATE:
        date_to = MAX_FUTURE_DATE

    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from

    if date_from and date_to and (date_to - date_from).days > MAX_RANGE_DAYS:
        date_from = date_to - timedelta(days=MAX_RANGE_DAYS)

    return date_from, date_to


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
        'total_customers': Lead.objects.filter(agent=request.user).values('email').distinct().count(),
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

    # Recent inquiries
    recent_inquiries = PropertyInquiry.objects.filter(
        agent_profile__user=request.user
    ).select_related('related_property').order_by('-created_at')[:5]
    
    context = {
        'agent_profile': agent_profile,
        'stats': stats,
        'recent_properties': recent_properties,
        'recent_leads': recent_leads,
        'recent_inquiries': recent_inquiries,
        'upcoming_visits': upcoming_visits,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'agent/dashboard.html', context)


@login_required
def profile(request):
    """View agent profile"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
        
    agent_profile = get_object_or_404(AgentProfile, user=request.user)
    
    # Get statistics
    total_properties = Property.objects.filter(seller=request.user).count()
    total_leads = Lead.objects.filter(property__seller=request.user).count()
    
    stats = {
        'total_properties': total_properties,
        'total_leads': total_leads,
    }
    
    context = {
        'agent_profile': agent_profile,
        'user': request.user,
        'stats': stats,
    }
    
    return render(request, 'agent/profile.html', context)


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


def _agent_listing_limit_response(request, check):
    """
    Build the HTTP response for a failed listing-eligibility check.
    Preserves the existing UX (plans redirect or limit modal).
    """
    if check.redirect_to_plans:
        messages.warning(request, check.message)
        return redirect('public:subscription_plans')
    return render(
        request,
        'agent/property_type_select.html',
        {
            'base_template': 'agent/agent_base.html',
            'limit_message': check.message,
            'limit_title': check.title,
        },
    )


def _enforce_agent_property_listing(request, user_role, subscription=SUBSCRIPTION_UNSET):
    """
    Run subscription listing validation for agents.
    Returns an HttpResponse when blocked; otherwise None.
    """
    if user_role != 'agent':
        return None
    check = check_property_listing_eligibility(
        request.user, subscription=subscription
    )
    if check.allowed:
        return None
    return _agent_listing_limit_response(request, check)


@login_required
def property_type_select(request):
    """Select property type before adding"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner', 'admin'] and not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Access denied. This page is only accessible to agents, owners, or admins.")

    blocked = _enforce_agent_property_listing(request, user_role)
    if blocked is not None:
        return blocked

    base_template = 'administration/admin_base.html' if (user_role == 'admin' or request.user.is_superuser or request.user.is_staff) else 'agent/agent_base.html'
    return render(request, 'agent/property_type_select.html', {'base_template': base_template})


@login_required
def property_add(request, property_type):
    """Add a new property with subscription-based listing limit validation."""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner', 'admin'] and not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Access denied. This page is only accessible to agents, owners, or admins.")

    # Gate form access for agents (inactive/expired/at-limit) before they fill the form
    blocked = _enforce_agent_property_listing(request, user_role)
    if blocked is not None:
        return blocked

    is_admin = user_role == 'admin' or request.user.is_superuser or request.user.is_staff
    if request.method == 'POST':
        # Use AgriculturalLandForm for land properties
        if property_type == 'land':
            form = AgriculturalLandForm(request.POST, request.FILES)
        else:
            form = PropertyForm(request.POST, request.FILES)

        if form.is_valid():
            # Re-validate on Submit Property under a lock so concurrent posts cannot bypass limits
            if user_role == 'agent':
                with transaction.atomic():
                    # Lock only UserSubscription — plan FK is nullable, so
                    # FOR UPDATE + OUTER JOIN fails on PostgreSQL.
                    locked_sub = (
                        UserSubscription.objects
                        .select_for_update(of=('self',))
                        .select_related('plan')
                        .filter(user_id=request.user.pk)
                        .first()
                    )
                    blocked = _enforce_agent_property_listing(
                        request, user_role, subscription=locked_sub
                    )
                    if blocked is not None:
                        return blocked
                    property_obj = _save_new_property(
                        form, request, property_type, is_admin=False
                    )
            else:
                property_obj = _save_new_property(
                    form, request, property_type, is_admin=is_admin
                )

            if is_admin:
                messages.success(request, "Property created successfully!")
                return redirect('admin_dash:admin-property-list')
            messages.success(
                request,
                "Property created successfully! It's pending admin approval.",
            )
            return redirect('agent:property_list')
        else:
            print("Form errors:", form.errors)
            # Build a clean, human-readable error message
            error_fields = []
            for field, errors in form.errors.items():
                field_label = form.fields[field].label or field.replace('_', ' ').title()
                error_fields.append(f"{field_label}: {', '.join(errors)}")
            error_summary = " | ".join(error_fields)
            messages.error(request, f"Please fix the following errors: {error_summary}")
    else:
        # Use appropriate form based on property_type
        if property_type == 'land':
            form = AgriculturalLandForm()
        else:
            initial_category = 'Apartments' if property_type == 'house' else 'Plots'
            form = PropertyForm(initial={'property_type': 'sale', 'category': initial_category})

    base_template = 'administration/admin_base.html' if is_admin else 'agent/agent_base.html'
    context = {
        'form': form,
        'property_type': property_type,
        'title': f'Add {property_type.title()}',
        'base_template': base_template
    }

    # Use different template for agricultural land
    if property_type == 'land':
        return render(request, 'agent/agricultural_land_form.html', context)
    else:
        return render(request, 'agent/property_form.html', context)


def _save_new_property(form, request, property_type, is_admin=False):
    """Persist a new property and its gallery images using the existing add workflow."""
    property_obj = form.save(commit=False)
    property_obj.seller = request.user
    if is_admin:
        property_obj.status = 'approved'
        property_obj.is_admin_list = True
    else:
        property_obj.status = 'pending'
        property_obj.created_by = request.user
        property_obj.last_updated_by = request.user

    if property_type == 'land':
        property_obj.property_type = 'sale'
        property_obj.category = 'Plots'
    elif property_type == 'house':
        property_obj.property_type = 'sale'
        property_obj.category = 'Apartments'

    # Slug is generated/deduplicated in Property.save()
    property_obj.save()

    for image in request.FILES.getlist('gallery_images'):
        try:
            validate_image_file(image)
            PropertyImage.objects.create(property=property_obj, image=image, category='General')
        except ValidationError:
            pass

    return property_obj


@login_required
def property_view_details(request, pk):
    """View single property details"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner', 'admin'] and not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Access denied. This page is only accessible to agents, owners, or admins.")

    is_admin = user_role == 'admin' or request.user.is_superuser or request.user.is_staff
    if is_admin:
        property_obj = get_object_or_404(Property.objects.select_related('seller'), pk=pk)
    else:
        property_obj = get_object_or_404(Property.objects.select_related('seller'), pk=pk, seller=request.user)

    images = property_obj.images.all()

    context = {
        'property': property_obj,
        'images': images,
    }

    return render(request, 'agent/property_detail.html', context)

@login_required
def property_edit(request, pk):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner', 'admin'] and not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Access denied. This page is only accessible to agents, owners, or admins.")
    """Edit an existing property"""
    is_admin = user_role == 'admin' or request.user.is_superuser or request.user.is_staff
    if is_admin:
        property_obj = get_object_or_404(Property.objects.select_related('seller'), pk=pk)
    else:
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
            
            # Save multiple images to the PropertyImage gallery table
            gallery_images = request.FILES.getlist('gallery_images')
            for image in gallery_images:
                try:
                    validate_image_file(image)
                    PropertyImage.objects.create(property=property_obj, image=image, category='General')
                except ValidationError:
                    pass
                
            messages.success(request, "Property updated successfully!")
            if is_admin:
                return redirect('admin_dash:admin-property-list')
            else:
                return redirect('agent:property_list')
    else:
        # Use appropriate form based on property_type
        if property_type == 'land':
            form = AgriculturalLandForm(instance=property_obj)
        else:
            form = PropertyForm(instance=property_obj)
    
    # Get property images
    images = property_obj.images.all()
    
    base_template = 'administration/admin_base.html' if is_admin else 'agent/agent_base.html'
    context = {
        'form': form,
        'property': property_obj,
        'images': images,
        'property_type': property_type,
        'title': f'Edit Property - {property_obj.title}',
        'base_template': base_template
    }
    
    # Use different template for agricultural land
    if property_type == 'land':
        return render(request, 'agent/agricultural_land_form.html', context)
    else:
        return render(request, 'agent/property_form.html', context)


@login_required
@require_GET
def get_cities_by_state(request):
    """AJAX endpoint to get cities for a given state"""
    state = request.GET.get('state', '')
    if state:
        cities = LocationData.objects.filter(state=state).values_list('city', flat=True).distinct().order_by('city')
        return JsonResponse({'cities': list(cities)})
    return JsonResponse({'cities': []})


@login_required
def property_delete(request, pk):
    # Check if user is an agent
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner', 'admin'] and not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Access denied. This page is only accessible to agents, owners, or admins.")
    """Delete a property"""
    is_admin = user_role == 'admin' or request.user.is_superuser or request.user.is_staff
    if is_admin:
        property_obj = get_object_or_404(Property.objects.select_related('seller'), pk=pk)
    else:
        property_obj = get_object_or_404(Property.objects.select_related('seller'), pk=pk, seller=request.user)
    
    if request.method == 'POST':
        property_title = property_obj.title
        property_obj.delete()
        messages.success(request, f"Property '{property_title}' deleted successfully!")
        if is_admin:
            return redirect('admin_dash:admin-property-list')
        else:
            return redirect('agent:property_list')
    
    base_template = 'administration/admin_base.html' if is_admin else 'agent/agent_base.html'
    cancel_url = 'admin_dash:admin-property-list' if is_admin else 'agent:property_list'
    context = {
        'property': property_obj,
        'base_template': base_template,
        'cancel_url': cancel_url
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
    
    all_leads = Lead.objects.filter(agent=request.user)
    leads = all_leads.select_related('property').order_by('-created_at')
    
    # Stats for the top cards
    today = timezone.now().date()
    stats = {
        'total_leads': all_leads.count(),
        'new_leads': all_leads.filter(created_at__date=today).count(),
        'contacted_leads': all_leads.filter(status='contacted').count(),
        'qualified_leads': all_leads.filter(status='qualified').count(),
        'closed_won_leads': all_leads.filter(status='closed_won').count(),
    }
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    # Filter by source
    source_filter = request.GET.get('source')
    if source_filter:
        leads = leads.filter(source=source_filter)
    
    # Filter by date range
    date_from, date_to = get_safe_date_range(request)
    if date_from:
        leads = leads.filter(created_at__date__gte=date_from)
    if date_to:
        leads = leads.filter(created_at__date__lte=date_to)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(property__title__icontains=search_query)
        )
    
    # CSV Export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Phone', 'Email', 'Property', 'Status', 'Source', 'Priority', 'Created Date'])
        for lead in leads:
            writer.writerow([
                lead.name, lead.phone, lead.email,
                lead.property.title if lead.property else '-',
                lead.get_status_display(), lead.get_source_display(),
                lead.priority.title(), lead.created_at.strftime('%d %b %Y %I:%M %p')
            ])
        return response
    
    # Pagination
    paginator = Paginator(leads, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'leads': page_obj.object_list,
        'stats': stats,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'agent/lead_list.html', context)


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
def lead_add(request):
    """Add a new lead manually"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.agent = request.user
            lead.save()
            messages.success(request, "Lead added successfully!")
            return redirect('agent:lead_list')
    else:
        form = LeadForm()
    
    form.fields['property'].queryset = Property.objects.filter(seller=request.user)
    
    context = {
        'form': form,
        'title': 'Add New Lead'
    }
    
    return render(request, 'agent/lead_form.html', context)


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
    date_from, date_to = get_safe_date_range_with_future(request)
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
    """Agent document verification management page."""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")

    try:
        agent_profile = request.user.agent_profile
    except AgentProfile.DoesNotExist:
        agent_profile = AgentProfile.objects.create(user=request.user)

    form = VerificationDocumentForm()
    reupload_doc = None

    if request.method == 'POST':
        action = request.POST.get('action', 'submit')
        reupload_id = request.POST.get('reupload_id')

        if action == 'reupload' and reupload_id:
            reupload_doc = get_object_or_404(
                VerificationDocument,
                pk=reupload_id,
                agent=request.user,
                is_current=True,
            )
            if not reupload_doc.can_reupload:
                messages.error(request, "This document cannot be re-uploaded in its current status.")
                return redirect(request.path)

        form = VerificationDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc_type = form.cleaned_data['document_type']
            if not reupload_doc:
                already = VerificationDocument.objects.filter(
                    agent=request.user,
                    document_type=doc_type,
                    is_current=True,
                ).exclude(status__in=['rejected', 'reupload_required']).first()
                if already:
                    messages.error(
                        request,
                        f"You already have a {already.display_name} submission "
                        f"({already.get_status_display()}). "
                        "Use Re-upload only if admin requests it."
                    )
                    return redirect(request.path)

            with transaction.atomic():
                if reupload_doc:
                    reupload_doc.is_current = False
                    reupload_doc.save(update_fields=['is_current', 'updated_at'])

                doc = form.save(commit=False)
                doc.agent = request.user
                doc.has_back_side = form.cleaned_data.get('has_back_side', True)
                if not doc.has_back_side:
                    doc.back_file = None
                doc.status = 'pending_review'
                doc.rejection_reason = ''
                if reupload_doc:
                    doc.replaces = reupload_doc
                    # Keep document type aligned with the rejected submission when re-uploading
                    doc.document_type = reupload_doc.document_type
                    if reupload_doc.document_type != 'other':
                        doc.document_name = ''
                    else:
                        doc.document_name = form.cleaned_data.get('document_name') or reupload_doc.document_name
                doc.save()

                VerificationDocument.objects.filter(
                    agent=request.user,
                    document_type=doc.document_type,
                    is_current=True,
                ).exclude(pk=doc.pk).update(is_current=False)

                VerificationDocument.sync_agent_profile_status(request.user)

            messages.success(
                request,
                f"{doc.display_name} submitted for verification successfully!"
            )
            return redirect(request.path)
        else:
            messages.error(request, "Please correct the errors below and try again.")

    submitted_docs = VerificationDocument.objects.filter(
        agent=request.user, is_current=True
    ).order_by('-submitted_at')

    submitted_type_codes = set(submitted_docs.values_list('document_type', flat=True))
    required_types = VerificationDocument.required_types()
    additional_types = VerificationDocument.additional_types()

    required_submitted_count = sum(
        1 for t in required_types if t['code'] in submitted_type_codes
    )
    required_verified_count = sum(
        1 for t in required_types
        if submitted_docs.filter(document_type=t['code'], status='verified').exists()
    )
    all_required_submitted = required_submitted_count == len(required_types)
    all_required_verified = required_verified_count == len(required_types)
    has_any_docs = submitted_docs.exists()
    has_pending_or_review = submitted_docs.filter(
        status__in=['pending_review', 'under_review']
    ).exists()
    admin_review_done = (
        agent_profile.verification_status in ['approved', 'rejected']
        or submitted_docs.filter(
            status__in=['verified', 'rejected', 'reupload_required']
        ).exists()
    ) and not has_pending_or_review and has_any_docs

    # Progress steps
    step_docs_submitted = has_any_docs
    step_under_review = has_any_docs and (
        has_pending_or_review or admin_review_done or all_required_verified
    )
    step_admin_review = admin_review_done or all_required_verified
    step_complete = agent_profile.is_verified or all_required_verified

    checklist_items = []
    for t in required_types:
        doc = submitted_docs.filter(document_type=t['code']).first()
        if doc and doc.status == 'verified':
            state = 'done'
            label = f"{t['label']} Verified"
        elif doc and doc.status in ('rejected', 'reupload_required'):
            state = 'rejected'
            label = f"{t['label']} — Re-upload Required"
        elif doc:
            state = 'done'
            label = f"{t['label']} Submitted"
        else:
            state = 'pending'
            label = f"{t['label']} Required"
        checklist_items.append({'label': label, 'state': state})

    for doc in submitted_docs.exclude(
        document_type__in=VerificationDocument.REQUIRED_DOCUMENT_TYPES
    ):
        if doc.status == 'verified':
            checklist_items.append({'label': f"{doc.display_name} Verified", 'state': 'done'})
        elif doc.status in ('rejected', 'reupload_required'):
            checklist_items.append({
                'label': f"{doc.display_name} — Re-upload Required",
                'state': 'rejected',
            })
        else:
            checklist_items.append({'label': f"{doc.display_name} Submitted", 'state': 'done'})

    if step_admin_review:
        checklist_items.append({'label': 'Admin Review Completed', 'state': 'done'})
    elif has_any_docs:
        checklist_items.append({'label': 'Admin Review', 'state': 'active'})
    else:
        checklist_items.append({'label': 'Admin Review', 'state': 'pending'})

    if step_complete:
        checklist_items.append({'label': 'Verification Complete', 'state': 'done'})
    else:
        checklist_items.append({'label': 'Verification Complete', 'state': 'locked'})

    context = {
        'agent_profile': agent_profile,
        'form': form,
        'submitted_docs': submitted_docs,
        'required_types': required_types,
        'additional_types': additional_types,
        'submitted_type_codes': submitted_type_codes,
        'verification_status': agent_profile.verification_status,
        'is_verified': agent_profile.is_verified or all_required_verified,
        'step_docs_submitted': step_docs_submitted,
        'step_under_review': step_under_review,
        'step_admin_review': step_admin_review,
        'step_complete': step_complete,
        'checklist_items': checklist_items,
        'all_required_submitted': all_required_submitted,
        'all_required_verified': all_required_verified,
        'title': 'Documents Verification',
    }

    return render(request, 'agent/document_list.html', context)


@login_required
def verification_document_detail(request, pk):
    """Return JSON details for a submitted verification document (View modal)."""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied.")

    doc = get_object_or_404(VerificationDocument, pk=pk, agent=request.user)

    def file_payload(field):
        if not field:
            return None
        name = field.name.rsplit('/', 1)[-1]
        url = field.url
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        return {
            'name': name,
            'url': url,
            'is_image': ext in ('jpg', 'jpeg', 'png', 'webp', 'gif'),
            'is_pdf': ext == 'pdf',
        }

    return JsonResponse({
        'id': doc.id,
        'document_type': doc.document_type,
        'document_type_display': doc.get_document_type_display(),
        'display_name': doc.display_name,
        'status': doc.status,
        'status_display': doc.get_status_display(),
        'rejection_reason': doc.rejection_reason or '',
        'submitted_at': doc.submitted_at.strftime('%d %b %Y'),
        'admin_reviewed_at': (
            doc.admin_reviewed_at.strftime('%d %b %Y') if doc.admin_reviewed_at else ''
        ),
        'has_back_side': doc.has_back_side,
        'can_reupload': doc.can_reupload,
        'front': file_payload(doc.front_file),
        'back': file_payload(doc.back_file) if doc.has_back_side else None,
    })


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
    
    base_queryset = Communication.objects.filter(agent=request.user)
    
    # Calculate stats dynamically
    total_sent = base_queryset.count()
    delivered = base_queryset.filter(status='delivered').count()
    opened = base_queryset.filter(status='read').count()
    failed = base_queryset.filter(status='failed').count()
    
    delivery_rate = f"{(delivered / total_sent * 100):.1f}%" if total_sent > 0 else "0%"
    open_rate = f"{(opened / total_sent * 100):.1f}%" if total_sent > 0 else "0%"
    failure_rate = f"{(failed / total_sent * 100):.1f}%" if total_sent > 0 else "0%"
    
    stats = {
        'total_sent': total_sent,
        'delivered': delivered,
        'opened': opened,
        'failed': failed,
        'delivery_rate': delivery_rate,
        'open_rate': open_rate,
        'failure_rate': failure_rate,
        'sent_change': "0% from last month" if total_sent == 0 else "+10%",
    }
    
    communications = base_queryset.select_related('lead', 'booking').order_by('-sent_at')
    
    # Filter by property
    property_filter = request.GET.get('property', '')
    if property_filter:
        communications = communications.filter(lead__property_id=property_filter)
        
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'opened':
            communications = communications.filter(status='read')
        else:
            communications = communications.filter(status=status_filter)
            
    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        communications = communications.filter(
            Q(recipient__icontains=q) |
            Q(subject__icontains=q) |
            Q(message__icontains=q) |
            Q(lead__name__icontains=q)
        )
        
    # Date range filtering
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        communications = communications.filter(sent_at__date__gte=date_from)
    if date_to:
        communications = communications.filter(sent_at__date__lte=date_to)
        
    date_range_display = "Select Date Range"
    if date_from and date_to:
        date_range_display = f"{date_from} to {date_to}"
    elif date_from:
        date_range_display = f"From {date_from}"
    elif date_to:
        date_range_display = f"Until {date_to}"
    
    # Properties belonging to or listed by the agent
    from Apps.PublicPage.models import Property
    agent_properties = Property.objects.filter(Q(seller=request.user) | Q(assigned_agent=request.user)).order_by('title')
    
    # Pagination
    paginator = Paginator(communications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'communications': page_obj.object_list,
        'stats': stats,
        'properties': agent_properties,
        'property_filter': property_filter,
        'status_filter': status_filter,
        'date_range': date_range_display,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': q,
    }
    
    return render(request, 'agent/communication_list.html', context)


@login_required
def communication_send(request):
    """Send a new communication"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = CommunicationForm(request.POST)
        if form.is_valid():
            communication = form.save(commit=False)
            communication.agent = request.user
            
            # Send Email
            try:
                send_mail(
                    subject=communication.subject,
                    message=communication.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[communication.recipient],
                    fail_silently=False,
                )
                communication.status = 'sent'
                communication.save()
                messages.success(request, "Email sent successfully!")
            except Exception as e:
                communication.status = 'failed'
                communication.save()
                messages.error(request, f"Failed to send email: {str(e)}")
                
            return redirect('agent:communication_list')
    else:
        form = CommunicationForm()
    
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
    inquiries = PropertyInquiry.objects.filter(
        agent_profile__user=request.user
    ).values('name', 'phone_number', 'email', 'enquiry_id', 'status', 'agent_profile', 'agent_profile__user__username', 'related_property__title', 'related_property__price').order_by('-created_at')
    # Combine and deduplicate
    customers = []
    seen = set()
    
    for booking in bookings:
        if not booking['customer_phone']:
            continue
        key = (booking['customer_phone'],)
        if key not in seen:
            customers.append({
                'name': booking['customer_name'],
                'phone': booking['customer_phone'],
                'email': booking['customer_email'],
                'source': 'Booking',
                'enquiry_id': '-',
                'status': '-',
                'agent_profile': '-',
            })
            seen.add(key)
            
    for inquiry in inquiries:
        if not inquiry['phone_number']:
            continue
        key = (inquiry['phone_number'],)
        if key not in seen:
            customers.append({
                'name': inquiry['name'],
                'phone': inquiry['phone_number'],
                'email': inquiry['email'],
                'source': 'Inquiry',
                'enquiry_id': inquiry['enquiry_id'],
                'status': inquiry['status'],
                'agent_profile': inquiry['agent_profile'],
                'agent_name': inquiry['agent_profile__user__username'],
                'property_title': inquiry['related_property__title'],
                'property_price': inquiry['related_property__price'],
            })
            seen.add(key)
    
    for lead in leads:
        if not lead['phone']:
            continue
        key = (lead['phone'],)
        if key not in seen:
            customers.append({
                'name': lead['name'],
                'phone': lead['phone'],
                'email': lead['email'],
                'source': 'Lead',
                'enquiry_id': '-',
                'status': '-',
                'agent_profile': '-',
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
    
    
    # Get customer's property inquiries
    inquiries = PropertyInquiry.objects.filter(
        agent_profile__user=request.user,
        phone_number=phone
    ).select_related('related_property')  

    # Mark 'new' inquiries as 'viewed' since agent is now viewing them
    inquiries.filter(status='new').update(status='viewed')  
    
    context = {
        'phone': phone,
        'bookings': bookings,
        'leads': leads,
        'visits': visits,
        'communications': communications,
        'inquiries': inquiries,
    }
    
    return render(request, 'agent/customer_detail.html', context)
   
     
@login_required
def change_password(request):
    """Change user password"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('agent:settings')
    else:
        form = PasswordChangeForm(request.user)
    
    # Add form-control class to all fields
    for field in form.fields:
        form.fields[field].widget.attrs['class'] = 'form-control'
    
    context = {
        'form': form,
    }
    
    return render(request, 'agent/change_password.html', context)


@login_required
def delete_account(request):
    """Delete user account"""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    if request.method == 'POST':
        # Delete the user account
        user = request.user
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect('public:home')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'agent/delete_account.html', context)


@login_required
def subscription_plans(request):
    """Subscription plans page for agents within the dashboard."""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied. This page is only accessible to agents or owners.")
    
    from Apps.Subscriptions.models import SubscriptionPlan
    
    plans = SubscriptionPlan.objects.prefetch_related('features', 'pricing_options').filter(is_active=True).order_by('display_order')
    
    return render(request, 'agent/subscription.html', {
        'plans': plans,
    })

@login_required
def document_verification(request):
    """KYC gate page for paid subscriptions — same workflow as Documents page."""
    user_role = get_user_role(request.user)
    if user_role not in ['agent', 'owner']:
        raise PermissionDenied("Access denied.")

    from Apps.Subscriptions.models import UserSubscription
    if not UserSubscription.objects.filter(user=request.user).exists():
        messages.info(request, "Please choose a subscription plan first.")
        return redirect('public:subscription_plans')

    # Reuse the full document management page
    return document_list(request)
