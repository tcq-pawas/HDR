from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Inquiry, Property, PropertyInquiry, PropertyImage, WebsiteEnquiry
from Apps.Agent.models import AgentProfile

# def home(request):
#     featured_properties = Property.objects.filter(is_featured=True).order_by('-created_at')[:6]
#     return render(request, 'public/home.html', {
#         'featured_properties': featured_properties
#     })

    
def home(request):
    # Show latest properties automatically — no manual "featured" toggling needed
    all_properties = Property.objects.all().order_by('-created_at')
    print("=== HOME VIEW CALLED, COUNT:", all_properties.count(), "===")

    farmland_listings = all_properties[:5]
    verified_properties = all_properties[5:9]

    return render(request, 'public/home.html', {
        'farmland_listings': farmland_listings,
        'verified_properties': verified_properties,
    })


def staff_required(user):
    return user.is_staff
@user_passes_test(staff_required)
def website_enquiry_list(request):
    """
    Shows all website enquiries in a table.
    Only staff / admin users can see this page.
    """
    enquiries = WebsiteEnquiry.objects.select_related('user').order_by('-created_at')
    return render(request, 'public/website_enquiry_list.html', {
        'enquiries': enquiries,
    })

    
def property_list(request):
    query = request.GET.get('q', '')
    properties = Property.objects.all().order_by('-created_at')
    
    if query:
        properties = properties.filter(
            Q(title__icontains=query) | 
            Q(location__icontains=query)
        )
    
    paginator = Paginator(properties, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'public/property_list.html', {
        'page_obj': page_obj,
        'query': query
    })

def property_detail(request, slug):
    property_obj = get_object_or_404(Property, slug=slug)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        PropertyInquiry.objects.create(
            property=property_obj,
            name=name,
            email=email,
            message=message
        )
        return redirect('public:property_detail', slug=slug)

    return render(request, 'public/property_detail.html', {
        'property': property_obj
    })

def about(request):
    return render(request, 'public/about.html')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def send_admin_email_notification(enquiry):
    from django.core.mail import send_mail
    from django.conf import settings
    from django.contrib.auth.models import User
    # pyrefly: ignore [missing-import]
    from Apps.Administration.models import SystemSettings
    from django.db.models import Q
    
    try:
        # Check if notification is enabled in system settings
        enabled_setting = SystemSettings.objects.filter(setting_key='ADMIN_ENQUIRY_NOTIFICATIONS_ENABLED').first()
        is_enabled = getattr(enabled_setting, 'setting_value', 'true').lower() == 'true'
        
        if not is_enabled:
            return
            
        # Get recipient email(s) from SystemSettings or fallback to admin users
        email_setting = SystemSettings.objects.filter(setting_key='ADMIN_NOTIFICATION_EMAIL').first()
        if email_setting and email_setting.setting_value:
            recipients = [email_setting.setting_value.strip()]
        else:
            # Get all active admin/superuser emails
            recipients = list(User.objects.filter(
                Q(is_superuser=True) | Q(groups__name='admin'),
                is_active=True
            ).exclude(email='').values_list('email', flat=True).distinct())
            
        if not recipients:
            recipients = [settings.DEFAULT_FROM_EMAIL or 'admin@heydayrealty.com']
            
        subject = f"New Website Enquiry #{enquiry.enquiry_id} - {enquiry.full_name}"
        message = f"""
Dear Admin,

You have received a new website enquiry from the contact form.

Enquiry Details:
----------------------------------------
ID: #{enquiry.enquiry_id}
Name: {enquiry.full_name}
Phone: {enquiry.phone_number or 'N/A'}
Email: {enquiry.email or 'N/A'}
Investment Budget: {enquiry.investment_budget or 'N/A'}

Message:
{enquiry.message}

----------------------------------------
To view and manage this enquiry, please log in to the Admin Dashboard:
http://localhost:8000/admin-dashboard/inquiries/{enquiry.id}/

Best regards,
HeyDay Realty System
"""
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="background-color: #0F766E; padding: 20px; text-align: center; color: white;">
                <h2 style="margin: 0; font-family: 'Poppins', sans-serif;">New Website Enquiry</h2>
            </div>
            <div style="padding: 24px; color: #1f2937; line-height: 1.6;">
                <p>Hello Admin,</p>
                <p>A new customer enquiry has been submitted on the website.</p>
                <h3 style="border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; color: #0F766E;">Enquiry Details</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; width: 150px; color: #4b5563;">Enquiry ID:</td>
                        <td style="padding: 8px 0;">#{enquiry.enquiry_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #4b5563;">Name:</td>
                        <td style="padding: 8px 0;">{enquiry.full_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #4b5563;">Phone Number:</td>
                        <td style="padding: 8px 0;">{enquiry.phone_number or '-'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #4b5563;">Email Address:</td>
                        <td style="padding: 8px 0;"><a href="mailto:{enquiry.email}" style="color: #0F766E;">{enquiry.email}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #4b5563;">Investment Budget:</td>
                        <td style="padding: 8px 0;">{enquiry.investment_budget or '-'}</td>
                    </tr>
                </table>
                
                <h3 style="border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; color: #0F766E;">Message</h3>
                <div style="background-color: #f8fafc; padding: 16px; border-radius: 6px; border: 1px solid #e2e8f0; white-space: pre-wrap; margin-bottom: 24px; color: #374151;">
                    {enquiry.message}
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="http://localhost:8000/admin-dashboard/inquiries/{enquiry.id}/" style="background-color: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">View in Admin Dashboard</a>
                </div>
            </div>
            <div style="background-color: #f8fafc; padding: 15px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e2e8f0;">
                This is an automated notification from HeyDay Realty.
            </div>
        </div>
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        pass


def contact(request):
    from django.contrib import messages
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone_number')
        email = request.POST.get('email')
        budget = request.POST.get('budget')
        message = request.POST.get('message')

        # Clean budget choice placeholder
        if budget == 'Select Budget Range':
            budget = '-'

        enquiry = Inquiry.objects.create(
            full_name=full_name,
            phone_number=phone,
            email=email,
            investment_budget=budget,
            message=message,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Trigger email notification
        send_admin_email_notification(enquiry)
        
        messages.success(request, 'Thank you! Your enquiry has been submitted. Our team will get back to you shortly.')
        return redirect('public:contact')
        
    return render(request, 'public/contact.html')

def career(request):
    return render(request, 'public/career.html')

def agents(request):
    """
    Public agents listing page with search filters
    """
    # Get all agents with profiles
    agents_list = AgentProfile.objects.select_related('user').all().order_by('-created_at')
    
    # Search filters
    search_query = request.GET.get('search', '')
    location = request.GET.get('location', '')
    specialization = request.GET.get('specialization', '')
    languages = request.GET.get('languages', '')
    
    # Apply filters
    if search_query:
        agents_list = agents_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(territory__icontains=search_query)
        )
    
    if location:
        agents_list = agents_list.filter(territory__icontains=location)
    
    if specialization:
        agents_list = agents_list.filter(bio__icontains=specialization)
    
    if languages:
        agents_list = agents_list.filter(bio__icontains=languages)
    
    # Pagination
    paginator = Paginator(agents_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Popular searches
    popular_searches = [
        'Bangalore', 'Chennai', 'Hyderabad', 'Mumbai', 'Pune',
        'Farmland', 'Agricultural Land', 'Plantation', 'Investment'
    ]
    
    return render(request, 'public/agents.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'location': location,
        'specialization': specialization,
        'languages': languages,
        'popular_searches': popular_searches,
    })

def nri(request):
    return render(request, 'public/nri.html')

def subscription_plans(request):
    """
    Subscription plans page for agents.
    Displays pricing tiers and billing options.
    """
    # Pricing data - prepared for future Stripe integration
    pricing_plans = {
        'seed': {
            'name': 'Seed',
            'subtitle': 'Forever Free',
            'price': 0,
            'billing': '₹0/month',
            'button_text': 'Get Started Free',
            'features': [
                {'text': '5 Active Listings', 'included': True},
                {'text': 'Basic Dashboard', 'included': True},
                {'text': 'Buyer Inquiries', 'included': True},
                {'text': 'WhatsApp Contact', 'included': True},
                {'text': 'Basic Analytics', 'included': True},
                {'text': 'Featured Listings', 'included': False},
                {'text': 'Videos', 'included': False},
                {'text': 'Brochure Upload', 'included': False},
                {'text': 'Verified Agent Badge', 'included': False},
                {'text': 'Priority in Search', 'included': False},
                {'text': 'Advanced Lead Management', 'included': False},
                {'text': 'Property Analytics (Advanced)', 'included': False},
                {'text': 'Team Members (1 Only)', 'included': False},
                {'text': 'Priority Support (Email)', 'included': False},
            ]
        },
        'harvest': {
            'name': 'Harvest',
            'subtitle': 'Billed annually at ₹4,799',
            'price': 499,
            'billing': '₹499/month',
            'button_text': 'Choose Harvest Plan',
            'features': [
                {'text': '50 Active Listings', 'included': True},
                {'text': '5 Featured Listings', 'included': True},
                {'text': '25 Images per Property', 'included': True},
                {'text': 'Videos', 'included': True},
                {'text': 'Brochure Upload', 'included': True},
                {'text': 'Verified Agent Badge', 'included': True},
                {'text': 'High Priority in Search', 'included': True},
                {'text': 'Advanced Lead Management', 'included': True},
                {'text': 'Property Analytics (Advanced)', 'included': True},
                {'text': 'WhatsApp Leads', 'included': True},
                {'text': 'Team Members (Up to 3)', 'included': True},
                {'text': 'Priority Support', 'included': True},
            ]
        },
        'legacy': {
            'name': 'Legacy',
            'subtitle': 'Billed annually at ₹9,599',
            'price': 999,
            'billing': '₹999/month',
            'button_text': 'Choose Legacy Plan',
            'features': [
                {'text': 'Unlimited Active Listings', 'included': True},
                {'text': 'Unlimited Featured Listings', 'included': True},
                {'text': 'Unlimited Images per Property', 'included': True},
                {'text': 'Videos', 'included': True},
                {'text': 'Brochure Upload', 'included': True},
                {'text': 'Premium Verified Badge', 'included': True},
                {'text': 'Highest Priority in Search', 'included': True},
                {'text': 'Premium CRM (Lead Management)', 'included': True},
                {'text': 'Property Analytics (Advanced + Reports)', 'included': True},
                {'text': 'WhatsApp Leads', 'included': True},
                {'text': 'Unlimited Team Members', 'included': True},
                {'text': 'Dedicated Support', 'included': True},
            ]
        }
    }
    
    # Billing periods with discounts
    billing_periods = {
        '1_month': {'label': '1 Month', 'discount': 0},
        '3_months': {'label': '3 Months', 'discount': 10},
        '6_months': {'label': '6 Months', 'discount': 15},
        '12_months': {'label': '12 Months', 'discount': 20},
    }
    
    return render(request, 'public/subscription/subscription.html', {
        'pricing_plans': pricing_plans,
        'billing_periods': billing_periods,
    })

def agent_profile(request, agent_id=None):
    """
    Public agent profile page with detailed information,
    listed properties, and reviews.
    """
    from django.shortcuts import get_object_or_404
    
    # Get agent profile
    agent = get_object_or_404(AgentProfile, id=agent_id)
    
    # Get agent's listed properties (active and approved)
    agent_properties = Property.objects.filter(
        seller=agent.user,
        is_active=True,
        status='approved',
        show_to_public=True
    ).prefetch_related('images').order_by('-created_at')
    
    # Calculate statistics
    active_listings = agent_properties.count()
    properties_sold = agent.user.bookings.count() if hasattr(agent.user, 'bookings') else 0
    years_experience = 1  # Default, could be calculated from created_at
    rating = 4.8  # Default rating, could be calculated from reviews
    response_rate = 95  # Default response rate
    
    # Sample reviews data (in production, this would come from a Review model)
    sample_reviews = [
        {
            'name': 'Rajesh Kumar',
            'avatar': 'https://randomuser.me/api/portraits/men/32.jpg',
            'rating': 5,
            'review': 'Excellent service! Very professional and knowledgeable about farmland investments.',
            'date': '2 weeks ago'
        },
        {
            'name': 'Priya Sharma',
            'avatar': 'https://randomuser.me/api/portraits/women/44.jpg',
            'rating': 4,
            'review': 'Good experience. Helped me find the perfect agricultural land for my needs.',
            'date': '1 month ago'
        },
        {
            'name': 'Amit Patel',
            'avatar': 'https://randomuser.me/api/portraits/men/67.jpg',
            'rating': 5,
            'review': 'Highly recommended. Very responsive and transparent throughout the process.',
            'date': '1 month ago'
        }
    ]
    
    context = {
        'agent': agent,
        'agent_properties': agent_properties,
        'active_listings': active_listings,
        'properties_sold': properties_sold,
        'years_experience': years_experience,
        'rating': rating,
        'response_rate': response_rate,
        'reviews': sample_reviews,
    }
    
    return render(request, 'public/agent_profile.html', context)
