from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Inquiry, Property, PropertyInquiry, PropertyImage, WebsiteEnquiry

def home(request):
    featured_properties = Property.objects.filter(is_featured=True).order_by('-created_at')[:6]
    return render(request, 'public/home.html', {
        'featured_properties': featured_properties
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

def media_page(request):
    images = PropertyImage.objects.select_related('property').all().order_by('-id')
    categories = PropertyImage.IMAGE_CATEGORIES
    
    return render(request, 'public/media.html', {
        'images': images,
        'categories': categories
    })

def career(request):
    return render(request, 'public/career.html')

def nri(request):
    return render(request, 'public/nri.html')

