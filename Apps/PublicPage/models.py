from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

class Property(models.Model):
    PROPERTY_TYPES = (
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    )
    CATEGORY_CHOICES = (
        ('Apartments', 'Apartments / Condos'),
        ('Villas', 'Villas / Independent Houses'),
        ('Commercial', 'Commercial Properties'),
        ('Luxury', 'Luxury Properties'),
        ('Plots', 'Plots / Land'),
    )
    
    # Basic public information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=200)
    property_type = models.CharField(max_length=10, choices=PROPERTY_TYPES, default='sale')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Apartments')
    
    # Seller and Status for Approval Workflow
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_properties', null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    
    # Limited public description
    public_description = models.TextField(
        help_text="Brief description shown to public visitors (max 200 characters)",
        max_length=200
    )
    
    # Detailed information (only visible to authenticated users)
    description = models.TextField(
        help_text="Full description only visible to authenticated users"
    )
    
    # Property details (public)
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    area_sqft = models.PositiveIntegerField()
    
    # Investment details (authenticated users only)
    investment_opportunity = models.BooleanField(default=False)
    expected_roi = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Expected ROI percentage (investors only)"
    )
    minimum_investment = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Minimum investment amount (investors only)"
    )
    
    # Visibility controls
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    show_to_public = models.BooleanField(
        default=True,
        help_text="Show property to unauthenticated visitors"
    )
    requires_authentication = models.BooleanField(
        default=False,
        help_text="Require authentication to view full details"
    )
    
    # Access control
    allowed_roles = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Users'),
            ('customer', 'Customers Only'),
            ('investor', 'Investors Only'),
            ('admin', 'Admin Only'),
        ],
        default='all',
        help_text="Roles that can access this property"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def can_view_public(self):
        """Check if property can be viewed by unauthenticated users"""
        return self.is_active and self.show_to_public

    def can_access_by_role(self, user):
        """Check if user can access this property based on role"""
        if not self.is_active:
            return False
        
        if self.allowed_roles == 'all':
            return True
        
        if not user.is_authenticated:
            return False
        
        from Apps.Administration.auth_utils import get_user_role
        user_role = get_user_role(user)
        
        return user_role == self.allowed_roles

    def get_public_data(self):
        """Get data that should be visible to public users"""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'price': self.price,
            'location': self.location,
            'property_type': self.property_type,
            'category': self.category,
            'public_description': self.public_description,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'area_sqft': self.area_sqft,
            'is_featured': self.is_featured,
        }

    def get_authenticated_data(self, user):
        """Get data for authenticated users based on their role"""
        if not self.can_access_by_role(user):
            return self.get_public_data()
        
        base_data = self.get_public_data()
        base_data.update({
            'description': self.description,
            'investment_opportunity': self.investment_opportunity,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        })
        
        # Add investment details for investors
        from Apps.Administration.auth_utils import get_user_role
        user_role = get_user_role(user)
        
        if user_role == 'investor' and self.investment_opportunity:
            base_data.update({
                'expected_roi': self.expected_roi,
                'minimum_investment': self.minimum_investment,
            })
        
        return base_data

class PropertyImage(models.Model):
    IMAGE_CATEGORIES = (
        ('General', 'General'),
        ('Interiors', 'Interiors'),
        ('Amenities', 'Amenities'),
        ('Neighborhood', 'Neighborhood / Lifestyle'),
    )
    property = models.ForeignKey(Property, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='properties/')
    category = models.CharField(max_length=20, choices=IMAGE_CATEGORIES, default='General')

    def __str__(self):
        return f"Image for {self.property.title}"

class PropertyInquiry(models.Model):
    property = models.ForeignKey(Property, related_name='inquiries', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry from {self.name}"
