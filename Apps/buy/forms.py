from django import forms
from Apps.PublicPage.models import PropertyInquiry

class PropertySearchForm(forms.Form):
    """Form for filtering and searching properties"""
    
    PRICE_CHOICES = [
        ('', 'Select Price Range'),
        ('under_10_lac', 'Under ₹10 Lac'),
        ('10_50_lac', '₹10 Lac - ₹50 Lac'),
        ('50_lac_1cr', '₹50 Lac - ₹1 Cr'),
        ('1cr_10cr', '₹1 Cr - ₹10 Cr'),
        ('above_10cr', 'Above ₹10 Cr'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('', 'Select Property Type'),
        ('Agricultural', 'Agricultural'),
        ('Residential', 'Residential'),
        ('Commercial', 'Commercial'),
        ('Farm Land', 'Farm Land'),
        ('Plot', 'Plot'),
    ]
    
    AREA_CHOICES = [
        ('', 'Select Area'),
        ('1-5', '1-5'),
        ('5-10', '5-10'),
        ('10-20', '10-20'),
        ('20-50', '20-50'),
        ('50+', '50+'),
    ]
    
    AREA_UNIT_CHOICES = [
        ('Acre', 'Acre'),
        ('Bigha', 'Bigha'),
        ('Hectare', 'Hectare'),
        ('Sq Ft', 'Sq Ft'),
        ('Sq Yard', 'Sq Yard'),
    ]
    
    STATUS_CHOICES = [
        ('', 'Select Status'),
        ('Active', 'Active'),
        ('Available', 'Available'),
        ('Sold', 'Sold'),
    ]
    
    SALE_BY_CHOICES = [
        ('', 'Sale By'),
        ('Owner', 'Owner'),
        ('Agent', 'Agent'),
        ('Builder', 'Builder'),
    ]
    
    SORT_CHOICES = [
        ('-created_at', 'Latest'),
        ('price', 'Price: Low to High'),
        ('-price', 'Price: High to Low'),
        ('area_sqft', 'Area: Low to High'),
        ('-area_sqft', 'Area: High to Low'),
    ]
    
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search locations across India',
            'autocomplete': 'off'
        })
    )
    
    price_range = forms.ChoiceField(
        required=False,
        choices=PRICE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    property_type = forms.ChoiceField(
        required=False,
        choices=PROPERTY_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    area_range = forms.ChoiceField(
        required=False,
        choices=AREA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    area_unit = forms.ChoiceField(
        required=False,
        choices=AREA_UNIT_CHOICES,
        initial='Sq Ft',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sale_by = forms.ChoiceField(
        required=False,
        choices=SALE_BY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class InquiryForm(forms.ModelForm):
    class Meta:
        model = PropertyInquiry
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your message or inquiry details here...'}),
        }
