from django import forms
from Apps.PublicPage.models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'price', 'location', 'property_type', 'category',
            'public_description', 'description', 'bedrooms', 'bathrooms', 'area_sqft',
            'investment_opportunity', 'expected_roi', 'minimum_investment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter property title'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'public_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Brief public description (max 200 characters)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed description visible to authenticated users'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'area_sqft': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'investment_opportunity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expected_roi': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected ROI % (e.g. 8.5)'}),
            'minimum_investment': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum investment amount'}),
        }
