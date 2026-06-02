from django import forms
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property, PropertyImage
from .models import AgentProfile


class PropertyForm(forms.ModelForm):
    """Form for creating and editing properties"""
    
    class Meta:
        model = Property
        fields = [
            'title', 'property_type', 'category', 'price', 'location',
            'public_description', 'description', 'bedrooms', 'bathrooms',
            'area_sqft', 'investment_opportunity', 'expected_roi', 'minimum_investment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Property Title'
            }),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price (₹)',
                'step': '0.01'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location'
            }),
            'public_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief public description (max 200 characters)',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Full description (only for authenticated users)'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of Bedrooms'
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of Bathrooms'
            }),
            'area_sqft': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Area in Sq Ft'
            }),
            'investment_opportunity': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'expected_roi': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expected ROI %',
                'step': '0.01'
            }),
            'minimum_investment': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimum Investment (₹)',
                'step': '0.01'
            }),
        }


class PropertyImageForm(forms.ModelForm):
    """Form for uploading property images"""
    
    class Meta:
        model = PropertyImage
        fields = ['image', 'category']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


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
        fields = ['phone', 'company_name', 'bio', 'profile_image']
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
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
