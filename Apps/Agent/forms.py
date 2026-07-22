from django import forms
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property, LocationData
from .models import (
    AgentProfile, Lead, LeadFollowUp, SiteVisit, Booking, 
    Installment, Commission, Document, Communication, MessageTemplate
)

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
        super().__init__(*args, **kwargs)

    def to_python(self, data):
        if isinstance(data, list) and data:
            data = data[0]
        return super().to_python(data)


class PropertyForm(forms.ModelForm):
    """Form for creating and editing properties"""
    featured_image = MultipleFileField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Base important fields required
        self.fields['title'].required = True
        self.fields['property_type'].required = True
        self.fields['category'].required = True
        self.fields['price'].required = True
        self.fields['location'].required = True
        self.fields['state'].required = True
        self.fields['district'].required = True
        self.fields['city'].required = True
        self.fields['pincode'].required = True
        self.fields['full_address'].required = True
        
        # Image required if not already uploaded
        if not (self.instance and self.instance.pk and self.instance.featured_image):
            self.fields['featured_image'].required = True
        else:
            self.fields['featured_image'].required = False

        # Make fields conditionally required based on property type
        if self.instance and self.instance.pk:
            # Editing existing property
            category = self.instance.category
            if category == 'Plots':
                # Land/Plot: make land fields required, house fields optional
                self.fields['plot_number'].required = False
                self.fields['total_area'].required = False
                self.fields['area_unit'].required = False
                self.fields['facing_direction'].required = False
                self.fields['land_category'].required = False
                # House fields remain optional
                self.fields['bedrooms'].required = False
                self.fields['bathrooms'].required = False
            else:
                # House/Villa: make house fields required, land fields optional
                self.fields['bedrooms'].required = False
                self.fields['bathrooms'].required = False
                self.fields['furnishing_status'].required = False
                self.fields['possession_status'].required = False
                # Land fields remain optional
                self.fields['plot_number'].required = False
                self.fields['total_area'].required = False
                self.fields['area_unit'].required = False
        else:
            # New property - all fields optional initially
            self.fields['plot_number'].required = False
            self.fields['total_area'].required = False
            self.fields['area_unit'].required = False
            self.fields['bedrooms'].required = False
        # Populate state choices dynamically
        state_choices = [('', 'Select State')]
        try:
            states = LocationData.objects.values_list('state', flat=True).distinct().order_by('state')
            state_list = [s for s in states if s]
            if self.instance and self.instance.pk and self.instance.state and self.instance.state not in state_list:
                state_list.append(self.instance.state)
            state_choices += [(s, s) for s in state_list]
        except Exception:
            pass
        self.fields['state'] = forms.CharField(
            required=True,
            widget=forms.Select(choices=state_choices, attrs={'class': 'form-select', 'id': 'state_select'})
        )
        if hasattr(self, 'instance') and self.instance and self.instance.pk and self.instance.state:
            self.fields['state'].initial = self.instance.state
        
        # Populate city choices dynamically based on existing instance state, or empty
        city_choices = [('', 'Select City')]
        try:
            city_list = []
            if self.instance and self.instance.pk and self.instance.state:
                cities = LocationData.objects.filter(state=self.instance.state).values_list('city', flat=True).distinct().order_by('city')
                city_list = [c for c in cities if c]
            elif self.data and self.data.get('state'):
                cities = LocationData.objects.filter(state=self.data.get('state')).values_list('city', flat=True).distinct().order_by('city')
                city_list = [c for c in cities if c]
            
            if self.instance and self.instance.pk and self.instance.city and self.instance.city not in city_list:
                city_list.append(self.instance.city)
                
            city_choices += [(c, c) for c in city_list]
        except Exception:
            pass
        self.fields['city'] = forms.CharField(
            required=True,
            widget=forms.Select(choices=city_choices, attrs={'class': 'form-select', 'id': 'city_select'})
        )
        if self.instance and self.instance.pk and self.instance.city:
            self.fields['city'].initial = self.instance.city
    
    class Meta:
        model = Property
        fields = [
            # Basic Information
            'title', 'property_type', 'category', 'price', 'location',
            'public_description', 'description',
            # Land-Specific Fields
            'plot_number', 'khasra_number', 'khata_number', 'registry_number',
            'total_area', 'area_unit', 'front_width', 'plot_depth', 'road_width',
            'facing_direction', 'corner_plot', 'land_category',
            'electricity_availability', 'water_availability', 'sewer_availability',
            'boundary_wall', 'irrigation_facility', 'nearby_facilities',
            'google_map_location', 'latitude', 'longitude',
            # House/Villa-Specific Fields
            'bedrooms', 'bathrooms', 'balconies', 'number_of_floors', 'property_age',
            'plot_area', 'built_up_area', 'carpet_area', 'furnishing_status',
            'parking_availability', 'garden', 'terrace', 'modular_kitchen',
            'store_room', 'power_backup', 'cctv', 'security', 'club_house_access',
            'swimming_pool', 'gym', 'smart_home_features', 'possession_status',
            # Pricing Management
            'price_per_sqft', 'booking_amount', 'negotiable', 'maintenance_charges',
            'down_payment', 'emi_availability',
            # Media Management
            'featured_image', 'property_video', 'drone_video', 'virtual_tour_360', 'floor_plan',
            # Document Management
            'registry_copy', 'sale_deed', 'mutation', 'building_approval',
            'completion_certificate', 'noc', 'layout_plan', 'property_brochure',
            # Location Management
            'state', 'district', 'city', 'locality', 'landmark', 'full_address', 'pincode',
            # Investment Details
            'investment_opportunity', 'expected_roi', 'minimum_investment',
            # Analytics & CRM
            'property_owner', 'source_tracking',
            # Visibility
            'is_featured', 'show_to_public', 'requires_authentication', 'allowed_roles',
        ]
        widgets = {
            # Basic Information
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Property Title'}),
            'property_type': forms.Select(attrs={'class': 'form-select', 'id': 'property_type_field'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price (₹)', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'public_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief public description (max 200 characters)', 'maxlength': '200'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Full description (only for authenticated users)'}),
            # Land-Specific Fields
            'plot_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plot Number'}),
            'khasra_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Khasra Number'}),
            'khata_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Khata Number'}),
            'registry_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registry Number'}),
            'total_area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Area', 'step': '0.01'}),
            'area_unit': forms.Select(attrs={'class': 'form-select'}),
            'front_width': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Front Width (in feet)', 'step': '0.01'}),
            'plot_depth': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Plot Depth (in feet)', 'step': '0.01'}),
            'road_width': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Road Width (in feet)', 'step': '0.01'}),
            'facing_direction': forms.Select(attrs={'class': 'form-select'}),
            'corner_plot': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'land_category': forms.Select(attrs={'class': 'form-select'}),
            'electricity_availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'water_availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sewer_availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'boundary_wall': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'irrigation_facility': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nearby_facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Nearby Facilities and Distances'}),
            'google_map_location': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Google Map Location URL'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude', 'step': '0.000001'}),
            # House/Villa-Specific Fields
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of Bedrooms'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of Bathrooms'}),
            'balconies': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of Balconies'}),
            'number_of_floors': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of Floors'}),
            'property_age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Property Age (in years)'}),
            'plot_area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Plot Area (in sq.ft)', 'step': '0.01'}),
            'built_up_area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Built-up Area (in sq.ft)', 'step': '0.01'}),
            'carpet_area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Carpet Area (in sq.ft)', 'step': '0.01'}),
            'furnishing_status': forms.Select(attrs={'class': 'form-select'}),
            'parking_availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'garden': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'terrace': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'modular_kitchen': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'store_room': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'power_backup': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cctv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'security': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'club_house_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'swimming_pool': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gym': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smart_home_features': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'possession_status': forms.Select(attrs={'class': 'form-select'}),
            # Pricing Management
            'price_per_sqft': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price Per Sq.ft', 'step': '0.01'}),
            'booking_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Booking Amount', 'step': '0.01'}),
            'negotiable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_charges': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maintenance Charges (monthly)', 'step': '0.01'}),
            'down_payment': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Down Payment', 'step': '0.01'}),
            'emi_availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Media Management
            'property_video': forms.FileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'drone_video': forms.FileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'virtual_tour_360': forms.URLInput(attrs={'class': 'form-control', 'placeholder': '360° Virtual Tour URL'}),
            'floor_plan': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            # Document Management
            'registry_copy': forms.FileInput(attrs={'class': 'form-control'}),
            'sale_deed': forms.FileInput(attrs={'class': 'form-control'}),
            'mutation': forms.FileInput(attrs={'class': 'form-control'}),
            'building_approval': forms.FileInput(attrs={'class': 'form-control'}),
            'completion_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'noc': forms.FileInput(attrs={'class': 'form-control'}),
            'layout_plan': forms.FileInput(attrs={'class': 'form-control'}),
            'property_brochure': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
            # Location Management
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'locality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Locality'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Landmark'}),
            'full_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            # Investment Details
            'investment_opportunity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expected_roi': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected ROI %', 'step': '0.01'}),
            'minimum_investment': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum Investment (₹)', 'step': '0.01'}),
            # Analytics & CRM
            'property_owner': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Property Owner Name'}),
            'source_tracking': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Source Tracking'}),
            # Visibility
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_to_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_authentication': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allowed_roles': forms.Select(attrs={'class': 'form-select'}),
        }


class AgriculturalLandForm(forms.ModelForm):
    """Form specifically for Agricultural Land properties"""
    featured_image = MultipleFileField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields for agricultural land
        self.fields['title'].required = True
        self.fields['agri_land_category'].required = True
        self.fields['total_area'].required = True
        self.fields['area_unit'].required = True
        self.fields['state'].required = True
        self.fields['district'].required = True
        self.fields['tehsil'].required = True
        self.fields['village'].required = False  # Will be added to model
        self.fields['pincode'].required = True
        self.fields['price'].required = True
        self.fields['full_address'].required = True
        
        # Image required if not already uploaded
        if not (self.instance and self.instance.pk and self.instance.featured_image):
            self.fields['featured_image'].required = True
        else:
            self.fields['featured_image'].required = False
            
        # Populate state choices dynamically
        state_choices = [('', 'Select State')]
        try:
            states = LocationData.objects.values_list('state', flat=True).distinct().order_by('state')
            state_list = [s for s in states if s]
            if self.instance and self.instance.pk and self.instance.state and self.instance.state not in state_list:
                state_list.append(self.instance.state)
            state_choices += [(s, s) for s in state_list]
        except Exception:
            pass
        self.fields['state'] = forms.CharField(
            required=True,
            widget=forms.Select(choices=state_choices, attrs={'class': 'form-select', 'id': 'state_select'})
        )
        if hasattr(self, 'instance') and self.instance and self.instance.pk and self.instance.state:
            self.fields['state'].initial = self.instance.state
    
    class Meta:
        model = Property
        fields = [
            # Basic Information
            'title', 'public_description', 'description',
            # Land Information
            'land_code', 'agri_land_category', 'land_status',
            # Area Information
            'total_area', 'area_unit',
            # Land Ownership Information
            'owner_name', 'owner_mobile', 'owner_email', 'ownership_type',
            # Revenue & Legal Information
            'khasra_number', 'khata_number', 'plot_number', 'registry_number',
            'revenue_village', 'tehsil', 'district', 'state', 'legal_status',
            # Land Characteristics
            'soil_type', 'land_shape', 'land_level', 'boundary_available', 'fencing_available',
            # Agricultural Features
            'irrigation_facility', 'borewell_available', 'canal_water', 'tube_well',
            'rainwater_harvesting', 'crop_suitability', 'current_usage',
            # Accessibility
            'road_connectivity', 'road_width', 'highway_distance',
            'nearest_village_distance', 'market_distance',
            'railway_station_distance', 'airport_distance',
            # Utilities
            'electricity_availability', 'water_availability',
            'solar_facility', 'farm_house_available', 'storage_facility',
            # Location
            'state', 'district', 'tehsil', 'village', 'pincode', 'full_address',
            'google_map_location', 'latitude', 'longitude',
            # Investment Information
            'price', 'price_per_acre', 'total_land_price', 'negotiable',
            'expected_roi', 'appreciation_potential', 'investment_type',
            # Media
            'featured_image', 'property_video', 'drone_video', 'virtual_tour_360',
            # Documents
            'registry_copy', 'sale_deed', 'layout_plan', 'property_brochure',
            # SEO & Marketing
            'seo_title', 'seo_description', 'keywords', 'property_highlights',
            # Visibility
            'is_featured', 'show_to_public', 'requires_authentication', 'allowed_roles',
        ]
        widgets = {
            # Basic Information
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Land Title'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'public_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief public description (max 200 characters)', 'maxlength': '200'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Full description'}),
            # Land Information
            'land_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'placeholder': 'Auto-generated'}),
            'agri_land_category': forms.Select(attrs={'class': 'form-select'}),
            'land_status': forms.Select(attrs={'class': 'form-select'}),
            # Area Information
            'total_area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Area', 'step': '0.01', 'id': 'total_area_input'}),
            'area_unit': forms.Select(attrs={'class': 'form-select', 'id': 'area_unit_select'}),
            # Land Ownership Information
            'owner_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner Name'}),
            'owner_mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner Mobile'}),
            'owner_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Owner Email'}),
            'ownership_type': forms.Select(attrs={'class': 'form-select'}),
            # Revenue & Legal Information
            'khasra_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Khasra Number'}),
            'khata_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Khata Number'}),
            'plot_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plot Number'}),
            'registry_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registry Number'}),
            'revenue_village': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Revenue Village'}),
            'tehsil': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tehsil'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'legal_status': forms.Select(attrs={'class': 'form-select'}),
            # Land Characteristics
            'soil_type': forms.Select(attrs={'class': 'form-select'}),
            'land_shape': forms.Select(attrs={'class': 'form-select'}),
            'land_level': forms.Select(attrs={'class': 'form-select'}),
            'boundary_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fencing_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Agricultural Features
            'irrigation_facility': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'borewell_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'canal_water': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tube_well': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rainwater_harvesting': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'crop_suitability': forms.Select(attrs={'class': 'form-select'}),
            'current_usage': forms.Select(attrs={'class': 'form-select'}),
            # Accessibility
            'road_connectivity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Road Connectivity'}),
            'road_width': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Road Width (ft)', 'step': '0.01'}),
            'highway_distance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Highway Distance (km)', 'step': '0.01'}),
            'nearest_village_distance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nearest Village Distance (km)', 'step': '0.01'}),
            'market_distance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Market Distance (km)', 'step': '0.01'}),
            'railway_station_distance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Railway Station Distance (km)', 'step': '0.01'}),
            'airport_distance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Airport Distance (km)', 'step': '0.01'}),
            # Utilities
            'electricity_availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'water_availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'solar_facility': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'farm_house_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'storage_facility': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Location
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'tehsil': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tehsil'}),
            'village': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'full_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'google_map_location': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Google Map Location URL'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude', 'step': '0.000001'}),
            # Investment Information
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Price (₹)', 'step': '0.01'}),
            'price_per_acre': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price Per Acre (₹)', 'step': '0.01'}),
            'total_land_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Land Price (₹)', 'step': '0.01'}),
            'negotiable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expected_roi': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected ROI %', 'step': '0.01'}),
            'appreciation_potential': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Appreciation Potential'}),
            'investment_type': forms.Select(attrs={'class': 'form-select'}),
            # Media
            'property_video': forms.FileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'drone_video': forms.FileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'virtual_tour_360': forms.URLInput(attrs={'class': 'form-control', 'placeholder': '360° Virtual Tour URL'}),
            # Documents
            'registry_copy': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
            'sale_deed': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
            'layout_plan': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,application/pdf'}),
            'property_brochure': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
            # SEO & Marketing
            'seo_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO Title'}),
            'seo_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'SEO Description'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Keywords (comma-separated)'}),
            'property_highlights': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Property Highlights'}),
            # Visibility
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_to_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_authentication': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allowed_roles': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-generate land code if not provided
        if not instance.land_code:
            from datetime import datetime
            import random
            prefix = 'AGRI'
            timestamp = datetime.now().strftime('%Y%m%d')
            random_num = random.randint(1000, 9999)
            instance.land_code = f'{prefix}-{timestamp}-{random_num}'
        
        # Set property type and category for agricultural land
        instance.property_type = 'sale'
        instance.category = 'Plots'
        
        if commit:
            instance.save()
        return instance


class AgentProfileForm(forms.ModelForm):
    """Form for updating agent profile"""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    class Meta:
        model = AgentProfile
        fields = ['phone', 'company_name', 'bio', 'profile_image', 'employee_id', 'territory', 'commission_rate', 'target_sales', 'notification_email', 'notification_sms', 'notification_whatsapp']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Bio'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Employee ID'
            }),
            'territory': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assigned Territory'
            }),
            'commission_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Commission Rate %',
                'step': '0.01'
            }),
            'target_sales': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monthly Sales Target',
                'step': '0.01'
            }),
            'notification_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_whatsapp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email


class LeadForm(forms.ModelForm):
    """Form for creating and editing leads"""
    
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'property', 'status', 'source', 'budget', 'requirements', 'notes', 'priority', 'expected_close_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lead Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'property': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Budget', 'step': '0.01'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Requirements'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class LeadFollowUpForm(forms.ModelForm):
    """Form for creating lead follow-ups"""
    
    class Meta:
        model = LeadFollowUp
        fields = ['follow_up_type', 'notes', 'scheduled_date']
        widgets = {
            'follow_up_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Follow-up notes'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class SiteVisitForm(forms.ModelForm):
    """Form for scheduling site visits"""
    
    class Meta:
        model = SiteVisit
        fields = ['property', 'lead', 'customer_name', 'customer_phone', 'customer_email', 'scheduled_date', 'status', 'notes']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Name'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Phone'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Customer Email'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class BookingForm(forms.ModelForm):
    """Form for creating bookings"""
    
    class Meta:
        model = Booking
        fields = ['property', 'lead', 'customer_name', 'customer_phone', 'customer_email', 'status', 'total_amount', 'token_amount', 'token_paid_date', 'notes']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Name'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer Phone'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Customer Email'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Amount', 'step': '0.01'}),
            'token_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Token Amount', 'step': '0.01'}),
            'token_paid_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class InstallmentForm(forms.ModelForm):
    """Form for creating installments"""
    
    class Meta:
        model = Installment
        fields = ['installment_number', 'amount', 'due_date', 'status', 'payment_method', 'receipt_number', 'notes']
        widgets = {
            'installment_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Payment Method'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receipt Number'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class CommissionForm(forms.ModelForm):
    """Form for creating commissions"""
    
    class Meta:
        model = Commission
        fields = ['commission_amount', 'commission_rate', 'sale_amount', 'status', 'due_date', 'paid_date', 'payment_method', 'notes']
        widgets = {
            'commission_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Commission Amount', 'step': '0.01'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Commission Rate %', 'step': '0.01'}),
            'sale_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Sale Amount', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'paid_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Payment Method'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes'}),
        }


class DocumentForm(forms.ModelForm):
    """Form for uploading documents"""
    
    class Meta:
        model = Document
        fields = ['property', 'booking', 'document_type', 'category', 'title', 'file', 'description', 'is_public']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'booking': forms.Select(attrs={'class': 'form-select'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document Title'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommunicationForm(forms.ModelForm):
    """Form for sending communications"""
    
    class Meta:
        model = Communication
        fields = ['communication_type', 'recipient', 'subject', 'message']
        widgets = {
            'communication_type': forms.Select(attrs={'class': 'form-select'}),
            'recipient': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Email Address'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Message'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['communication_type'].choices = [('email', 'Email')]


class MessageTemplateForm(forms.ModelForm):
    """Form for creating message templates"""
    
    class Meta:
        model = MessageTemplate
        fields = ['template_type', 'purpose', 'name', 'subject', 'content', 'variables', 'is_active']
        widgets = {
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'purpose': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Template Name'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Content'}),
            'variables': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Variables (JSON format)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
