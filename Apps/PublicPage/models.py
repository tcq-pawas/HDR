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
    
    AREA_UNIT_CHOICES = (
        ('sqft', 'Sq.ft'),
        ('sqyard', 'Sq.Yard'),
        ('acre', 'Acre'),
        ('bigha', 'Bigha'),
        ('hectare', 'Hectare'),
    )
    
    FACING_CHOICES = (
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
        ('north_east', 'North-East'),
        ('north_west', 'North-West'),
        ('south_east', 'South-East'),
        ('south_west', 'South-West'),
    )
    
    LAND_CATEGORY_CHOICES = (
        ('agricultural', 'Agricultural'),
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
    )
    
    FURNISHING_CHOICES = (
        ('unfurnished', 'Unfurnished'),
        ('semi_furnished', 'Semi-Furnished'),
        ('fully_furnished', 'Fully-Furnished'),
    )
    
    POSSESSION_STATUS_CHOICES = (
        ('ready_to_move', 'Ready to Move'),
        ('under_construction', 'Under Construction'),
        ('new_launch', 'New Launch'),
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
    
    # Property details (public) - kept for backward compatibility
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.PositiveIntegerField(null=True, blank=True)
    area_sqft = models.PositiveIntegerField(null=True, blank=True)
    
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
    
    # ==================== Land-Specific Fields ====================
    plot_number = models.CharField(max_length=100, null=True, blank=True, help_text="Plot Number")
    khasra_number = models.CharField(max_length=100, null=True, blank=True, help_text="Khasra Number")
    khata_number = models.CharField(max_length=100, null=True, blank=True, help_text="Khata Number")
    registry_number = models.CharField(max_length=100, null=True, blank=True, help_text="Registry Number")
    total_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Total Area")
    area_unit = models.CharField(max_length=20, choices=AREA_UNIT_CHOICES, null=True, blank=True, help_text="Area Unit")
    front_width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Front Width (in feet)")
    plot_depth = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Plot Depth (in feet)")
    road_width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Road Width (in feet)")
    facing_direction = models.CharField(max_length=20, choices=FACING_CHOICES, null=True, blank=True, help_text="Facing Direction")
    corner_plot = models.BooleanField(default=False, help_text="Corner Plot")
    land_category = models.CharField(max_length=20, choices=LAND_CATEGORY_CHOICES, null=True, blank=True, help_text="Land Category")
    electricity_availability = models.BooleanField(default=False, help_text="Electricity Availability")
    water_availability = models.BooleanField(default=False, help_text="Water Availability")
    sewer_availability = models.BooleanField(default=False, help_text="Sewer Availability")
    boundary_wall = models.BooleanField(default=False, help_text="Boundary Wall")
    irrigation_facility = models.BooleanField(default=False, help_text="Irrigation Facility")
    nearby_facilities = models.TextField(null=True, blank=True, help_text="Nearby Facilities and Distances")
    google_map_location = models.URLField(null=True, blank=True, help_text="Google Map Location")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude")
    
    # ==================== House/Villa-Specific Fields ====================
    bhk_configuration = models.CharField(max_length=20, null=True, blank=True, help_text="BHK Configuration (e.g., 2BHK, 3BHK)")
    balconies = models.PositiveIntegerField(null=True, blank=True, help_text="Number of Balconies")
    number_of_floors = models.PositiveIntegerField(null=True, blank=True, help_text="Number of Floors")
    property_age = models.PositiveIntegerField(null=True, blank=True, help_text="Property Age (in years)")
    plot_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Plot Area (in sq.ft)")
    built_up_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Built-up Area (in sq.ft)")
    carpet_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Carpet Area (in sq.ft)")
    furnishing_status = models.CharField(max_length=20, choices=FURNISHING_CHOICES, null=True, blank=True, help_text="Furnishing Status")
    parking_availability = models.BooleanField(default=False, help_text="Parking Availability")
    garden = models.BooleanField(default=False, help_text="Garden")
    terrace = models.BooleanField(default=False, help_text="Terrace")
    modular_kitchen = models.BooleanField(default=False, help_text="Modular Kitchen")
    store_room = models.BooleanField(default=False, help_text="Store Room")
    power_backup = models.BooleanField(default=False, help_text="Power Backup")
    cctv = models.BooleanField(default=False, help_text="CCTV")
    security = models.BooleanField(default=False, help_text="Security")
    club_house_access = models.BooleanField(default=False, help_text="Club House Access")
    swimming_pool = models.BooleanField(default=False, help_text="Swimming Pool")
    gym = models.BooleanField(default=False, help_text="Gym")
    smart_home_features = models.BooleanField(default=False, help_text="Smart Home Features")
    possession_status = models.CharField(max_length=20, choices=POSSESSION_STATUS_CHOICES, null=True, blank=True, help_text="Possession Status")
    
    # ==================== Pricing Management Fields ====================
    price_per_sqft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price Per Sq.ft")
    booking_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Booking Amount")
    negotiable = models.BooleanField(default=False, help_text="Negotiable")
    maintenance_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maintenance Charges (monthly)")
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Down Payment")
    emi_availability = models.BooleanField(default=False, help_text="EMI Availability")
    
    # ==================== Media Management Fields ====================
    featured_image = models.ImageField(upload_to='properties/featured/', null=True, blank=True, help_text="Featured Image")
    property_video = models.FileField(upload_to='properties/videos/', null=True, blank=True, help_text="Property Video")
    drone_video = models.FileField(upload_to='properties/videos/drone/', null=True, blank=True, help_text="Drone Video")
    virtual_tour_360 = models.URLField(null=True, blank=True, help_text="360° Virtual Tour URL")
    floor_plan = models.ImageField(upload_to='properties/floorplans/', null=True, blank=True, help_text="Floor Plan Image")
    
    # ==================== Document Management Fields ====================
    registry_copy = models.FileField(upload_to='properties/documents/registry/', null=True, blank=True, help_text="Registry Copy")
    sale_deed = models.FileField(upload_to='properties/documents/sale_deed/', null=True, blank=True, help_text="Sale Deed")
    mutation = models.FileField(upload_to='properties/documents/mutation/', null=True, blank=True, help_text="Mutation Document")
    building_approval = models.FileField(upload_to='properties/documents/approval/', null=True, blank=True, help_text="Building Approval")
    completion_certificate = models.FileField(upload_to='properties/documents/completion/', null=True, blank=True, help_text="Completion Certificate")
    noc = models.FileField(upload_to='properties/documents/noc/', null=True, blank=True, help_text="NOC Document")
    layout_plan = models.FileField(upload_to='properties/documents/layout/', null=True, blank=True, help_text="Layout Plan")
    property_brochure = models.FileField(upload_to='properties/documents/brochure/', null=True, blank=True, help_text="Property Brochure PDF")
    
    # ==================== Location Management Fields ====================
    state = models.CharField(max_length=100, null=True, blank=True, help_text="State")
    district = models.CharField(max_length=100, null=True, blank=True, help_text="District")
    city = models.CharField(max_length=100, null=True, blank=True, help_text="City")
    locality = models.CharField(max_length=200, null=True, blank=True, help_text="Locality")
    landmark = models.CharField(max_length=200, null=True, blank=True, help_text="Landmark")
    full_address = models.TextField(null=True, blank=True, help_text="Full Address")
    pincode = models.CharField(max_length=10, null=True, blank=True, help_text="Pincode")
    
    # ==================== Analytics and CRM Fields ====================
    assigned_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_properties', help_text="Assigned Agent")
    property_owner = models.CharField(max_length=200, null=True, blank=True, help_text="Property Owner Name")
    property_views_count = models.PositiveIntegerField(default=0, help_text="Property Views Count")
    inquiry_count = models.PositiveIntegerField(default=0, help_text="Inquiry Count")
    lead_count = models.PositiveIntegerField(default=0, help_text="Lead Count")
    source_tracking = models.CharField(max_length=100, null=True, blank=True, help_text="Source Tracking")
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_properties', help_text="Last Updated By")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_properties', help_text="Created By")
    
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
