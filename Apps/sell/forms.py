from django import forms
from Apps.PublicPage.models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'price', 'location', 'property_type', 'category',
            'public_description', 'description', 'bedrooms', 'bathrooms', 'area_sqft',
            'project_size_acre', 'plot_sizes', 'water_source', 'road_access', 'soil_type', 
            'plantation_type','registry_status', 'google_map_link', 'farmhouse_available',
            'investment_opportunity', 'expected_roi', 'minimum_investment', 'project_highlights',
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
            'project_size_acre': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Example: 25 Acre'}),
            'plot_sizes': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Example: 5000 Sq Ft - 1 Acre'}),
            'water_source': forms.TextInput(attrs={'class': 'form-control'}),
            'road_access': forms.TextInput(attrs={'class': 'form-control'}),
            'soil_type': forms.TextInput(attrs={'class': 'form-control'}),
            'plantation_type': forms.TextInput(attrs={'class': 'form-control'}),
            'registry_status': forms.TextInput(attrs={'class': 'form-control'}),
            'google_map_link': forms.URLInput(attrs={'class': 'form-control'}),
            'farmhouse_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'project_highlights': forms.Textarea(attrs={'class': 'form-control','rows': 5,'placeholder': 'One highlight per line'
                }),
                    }
