from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Property, PropertyInquiry, PropertyImage

def home(request):
    featured_properties = Property.objects.filter(is_featured=True).order_by('-created_at')[:6]
    return render(request, 'public/home.html', {
        'featured_properties': featured_properties
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

def contact(request):
    if request.method == 'POST':
        # Handle contact form logic (e.g. send email)
        pass
    return render(request, 'public/contact.html')

def media_page(request):
    images = PropertyImage.objects.select_related('property').all().order_by('-id')
    categories = PropertyImage.IMAGE_CATEGORIES
    
    return render(request, 'public/media.html', {
        'images': images,
        'categories': categories
    })
