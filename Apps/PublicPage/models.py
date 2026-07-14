from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
import random

# Deferred import to avoid circular imports at module load time
def _get_user_role(user):
    # pyrefly: ignore [missing-import]
    from Apps.Administration.auth_utils import get_user_role
    return get_user_role(user)

class Property(models.Model):
    PROPERTY_TYPES = (
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    )
    # CATEGORY_CHOICES = (
    #     ('Apartments', 'Apartments / Condos'),
    #     ('Villas', 'Villas / Independent Houses'),
    #     ('Commercial', 'Commercial Properties'),
    #     ('Luxury', 'Luxury Properties'),
    #     ('Plots', 'Plots / Land'),
    # )

    CATEGORY_CHOICES = (
    ('Managed Farmland', 'Managed Farmland'),
    ('Agricultural Land', 'Agricultural Land'),
    ('Farm Plots', 'Farm Plots'),
    ('Weekend Farm', 'Weekend Farm'),
    ('Investment Farmland', 'Investment Farmland'),
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
    
    # Agricultural Land Categories
    AGRI_LAND_CATEGORY_CHOICES = (
        ('agricultural_land', 'Agricultural Land'),
        ('farmland', 'Farmland'),
        ('plantation_land', 'Plantation Land'),
        ('organic_farming_land', 'Organic Farming Land'),
        ('agro_investment_land', 'Agro Investment Land'),
    )
    
    # Land Status
    LAND_STATUS_CHOICES = (
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('under_verification', 'Under Verification'),
    )
    
    # Area Units for Agricultural Land
    AGRI_AREA_UNIT_CHOICES = (
        ('acre', 'Acre'),
        ('bigha', 'Bigha'),
        ('hectare', 'Hectare'),
        ('guntha', 'Guntha'),
        ('sq_yard', 'Sq Yard'),
        ('sq_meter', 'Sq Meter'),
    )
    
    # Ownership Type
    OWNERSHIP_TYPE_CHOICES = (
        ('individual', 'Individual'),
        ('joint_ownership', 'Joint Ownership'),
        ('company', 'Company'),
        ('trust', 'Trust'),
    )
    
    # Legal Status
    LEGAL_STATUS_CHOICES = (
        ('clear_title', 'Clear Title'),
        ('under_verification', 'Under Verification'),
        ('litigation', 'Litigation'),
    )
    
    # Soil Type
    SOIL_TYPE_CHOICES = (
        ('black_soil', 'Black Soil'),
        ('red_soil', 'Red Soil'),
        ('alluvial_soil', 'Alluvial Soil'),
        ('sandy_soil', 'Sandy Soil'),
        ('mixed_soil', 'Mixed Soil'),
    )
    
    # Land Shape
    LAND_SHAPE_CHOICES = (
        ('square', 'Square'),
        ('rectangle', 'Rectangle'),
        ('irregular', 'Irregular'),
    )
    
    # Land Level
    LAND_LEVEL_CHOICES = (
        ('flat', 'Flat'),
        ('semi_flat', 'Semi Flat'),
        ('hilly', 'Hilly'),
    )
    
    # Crop Suitability
    CROP_SUITABILITY_CHOICES = (
        ('wheat', 'Wheat'),
        ('rice', 'Rice'),
        ('sugarcane', 'Sugarcane'),
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('mixed_farming', 'Mixed Farming'),
    )
    
    # Current Usage
    CURRENT_USAGE_CHOICES = (
        ('farming', 'Farming'),
        ('plantation', 'Plantation'),
        ('dairy', 'Dairy'),
        ('agro_investment', 'Agro Investment'),
        ('vacant_land', 'Vacant Land'),
    )
    
    # Investment Type
    INVESTMENT_TYPE_CHOICES = (
        ('agriculture', 'Agriculture'),
        ('long_term_investment', 'Long-Term Investment'),
        ('plantation', 'Plantation'),
        ('agro_business', 'Agro Business'),
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

    # Farmland Details
    project_size_acre = models.CharField(max_length=100, blank=True)

    plot_sizes = models.CharField(
        max_length=200,
        blank=True,
        help_text="Example: 5000 Sq Ft - 1 Acre"
    )

    water_source = models.CharField(max_length=200, blank=True)
    road_access = models.CharField(max_length=200, blank=True)
    soil_type = models.CharField(max_length=200, blank=True)
    plantation_type = models.CharField(max_length=200, blank=True)
    registry_status = models.CharField(max_length=100, blank=True)
    google_map_link = models.URLField(blank=True)
    farmhouse_available = models.BooleanField(default=False)
    
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
    
    # ==================== Agricultural Land-Specific Fields ====================
    # Land Information
    land_code = models.CharField(max_length=50, null=True, blank=True, unique=True, help_text="Auto-generated Land Code")
    agri_land_category = models.CharField(max_length=30, choices=AGRI_LAND_CATEGORY_CHOICES, null=True, blank=True, help_text="Agricultural Land Category")
    land_status = models.CharField(max_length=20, choices=LAND_STATUS_CHOICES, default='available', help_text="Land Status")
    
    # Land Ownership Information
    owner_name = models.CharField(max_length=200, null=True, blank=True, help_text="Owner Name")
    owner_mobile = models.CharField(max_length=20, null=True, blank=True, help_text="Owner Mobile")
    owner_email = models.EmailField(null=True, blank=True, help_text="Owner Email")
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_TYPE_CHOICES, null=True, blank=True, help_text="Ownership Type")
    
    # Revenue & Legal Information
    revenue_village = models.CharField(max_length=200, null=True, blank=True, help_text="Revenue Village")
    tehsil = models.CharField(max_length=200, null=True, blank=True, help_text="Tehsil")
    legal_status = models.CharField(max_length=20, choices=LEGAL_STATUS_CHOICES, null=True, blank=True, help_text="Legal Status")
    
    # Land Characteristics
    soil_type = models.CharField(max_length=20, choices=SOIL_TYPE_CHOICES, null=True, blank=True, help_text="Soil Type")
    land_shape = models.CharField(max_length=20, choices=LAND_SHAPE_CHOICES, null=True, blank=True, help_text="Land Shape")
    land_level = models.CharField(max_length=20, choices=LAND_LEVEL_CHOICES, null=True, blank=True, help_text="Land Level")
    boundary_available = models.BooleanField(default=False, help_text="Boundary Available")
    fencing_available = models.BooleanField(default=False, help_text="Fencing Available")
    
    # Agricultural Features
    borewell_available = models.BooleanField(default=False, help_text="Borewell Available")
    canal_water = models.BooleanField(default=False, help_text="Canal Water")
    tube_well = models.BooleanField(default=False, help_text="Tube Well")
    rainwater_harvesting = models.BooleanField(default=False, help_text="Rainwater Harvesting")
    crop_suitability = models.CharField(max_length=20, choices=CROP_SUITABILITY_CHOICES, null=True, blank=True, help_text="Crop Suitability")
    current_usage = models.CharField(max_length=20, choices=CURRENT_USAGE_CHOICES, null=True, blank=True, help_text="Current Usage")
    
    # Accessibility
    road_connectivity = models.CharField(max_length=200, null=True, blank=True, help_text="Road Connectivity")
    highway_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Highway Distance (km)")
    nearest_village_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Nearest Village Distance (km)")
    market_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Market Distance (km)")
    railway_station_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Railway Station Distance (km)")
    airport_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Airport Distance (km)")
    
    # Utilities
    solar_facility = models.BooleanField(default=False, help_text="Solar Facility")
    farm_house_available = models.BooleanField(default=False, help_text="Farm House Available")
    storage_facility = models.BooleanField(default=False, help_text="Storage Facility")
    
    # Investment Information
    price_per_acre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Price Per Acre")
    total_land_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Total Land Price")
    appreciation_potential = models.CharField(max_length=200, null=True, blank=True, help_text="Appreciation Potential")
    investment_type = models.CharField(max_length=30, choices=INVESTMENT_TYPE_CHOICES, null=True, blank=True, help_text="Investment Type")
    
    # SEO & Marketing
    seo_title = models.CharField(max_length=200, null=True, blank=True, help_text="SEO Title")
    seo_description = models.TextField(null=True, blank=True, help_text="SEO Description")
    keywords = models.CharField(max_length=500, null=True, blank=True, help_text="Keywords (comma-separated)")
    property_highlights = models.TextField(null=True, blank=True, default='')
    
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
    tehsil = models.CharField(max_length=200, null=True, blank=True, help_text="Tehsil")
    village = models.CharField(max_length=200, null=True, blank=True, help_text="Village")
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
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            qs = Property.objects.filter(slug=slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                qs = Property.objects.filter(slug=slug)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
            self.slug = slug
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
        
        user_role = _get_user_role(user)
        
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
        user_role = _get_user_role(user)
        
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

# contact form
class ContactInquiry(models.Model):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    budget = models.CharField(max_length=50, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.phone}"
    
    
#Inquiry model for admin panel
class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('follow_up', 'Follow Up'),
        ('interested', 'Interested'),
        ('site_visit_scheduled', 'Site Visit Scheduled'),
        ('converted', 'Converted'),
        ('closed', 'Closed'),
        # ('spam', 'Spam'),
    ]
    enquiry_id = models.CharField(max_length=5, unique=True, editable=False, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField()
    investment_budget = models.CharField(max_length=100, null=True, blank=True)
    investment_requirement = models.TextField(null=True, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    source = models.CharField(max_length=100, default='Website Contact Form')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    admin_notes = models.TextField(null=True, blank=True, help_text="Internal notes, visible only to admin")
    
    
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.enquiry_id:
            self.enquiry_id = self.generate_unique_id()
        super().save(*args, **kwargs)
        
    @staticmethod
    def generate_unique_id():
        while True:
            new_id = str(random.randint(10000, 99999))
            if not Inquiry.objects.filter(enquiry_id=new_id).exists():
                return new_id

    def __str__(self):
        return f"Enquiry #{self.enquiry_id} - {self.full_name}"


# ==================== WebsiteEnquiry Model ====================
class WebsiteEnquiry(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('follow_up', 'Follow Up'),
        ('interested', 'Interested'),
        ('site_visit_scheduled', 'Site Visit Scheduled'),
        ('converted', 'Converted'),
        ('closed', 'Closed'),
    ]

    BUDGET_CHOICES = [
        ('under_5L', 'Under ₹5 Lakh'),
        ('5L_10L', '₹5 Lakh – ₹10 Lakh'),
        ('10L_25L', '₹10 Lakh – ₹25 Lakh'),
        ('25L_50L', '₹25 Lakh – ₹50 Lakh'),
        ('50L_1Cr', '₹50 Lakh – ₹1 Crore'),
        ('above_1Cr', 'Above ₹1 Crore'),
    ]

    # Auto-generated unique enquiry ID (e.g. ENQ-84291)
    enquiry_id = models.CharField(max_length=10, unique=True, editable=False, blank=True)

    # Contact Information
    full_name = models.CharField(max_length=255, verbose_name="Full Name")
    phone_number = models.CharField(max_length=20, verbose_name="Phone Number")
    email = models.EmailField(verbose_name="Email Address")

    # Enquiry Details
    investment_budget = models.CharField(
        max_length=50,
        choices=BUDGET_CHOICES,
        null=True, blank=True,
        verbose_name="Investment Budget"
    )
    message = models.TextField(verbose_name="Message")

    # Status & Workflow
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Status"
    )

    # Admin-only Internal Notes
    admin_notes = models.TextField(
        null=True, blank=True,
        verbose_name="Admin Notes",
        help_text="Internal notes — visible only to admin"
    )

    # Tracking / Meta
    source = models.CharField(
        max_length=100,
        default='Website Contact Form',
        verbose_name="Source"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    # Optional System Info
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="IP Address"
    )
    user_agent = models.TextField(
        null=True, blank=True,
        verbose_name="User Agent"
    )

    # Linked User (if logged in)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='website_enquiries',
        verbose_name="User Interface"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Website Enquiry"
        verbose_name_plural = "Website Enquiries"

    def save(self, *args, **kwargs):
        if not self.enquiry_id:
            self.enquiry_id = self._generate_unique_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_id():
        while True:
            new_id = f"ENQ-{random.randint(10000, 99999)}"
            if not WebsiteEnquiry.objects.filter(enquiry_id=new_id).exists():
                return new_id

    def get_status_badge_class(self):
        """Returns Bootstrap badge class for the current status"""
        badge_map = {
            'new':                  'bg-primary',
            'contacted':            'bg-warning text-dark',
            'follow_up':            'bg-secondary',
            'interested':           'bg-purple',
            'site_visit_scheduled': 'bg-info',
            'converted':            'bg-success',
            'closed':               'bg-dark',
        }
        return badge_map.get(self.status, 'bg-secondary')

    def __str__(self):
        return f"{self.enquiry_id} — {self.full_name} ({self.get_status_display()})"


class LocationData(models.Model):
    """Model to store location data from CSV import"""
    geo_name_id = models.IntegerField(unique=True, primary_key=True)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    country = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    timezone = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=1)
    display_name = models.CharField(max_length=300)

    class Meta:
        verbose_name = "Location Data"
        verbose_name_plural = "Location Data"
        ordering = ['sort_order', 'city']
        db_table = 'location'

    def __str__(self):
        return f"{self.city}, {self.state}"
