from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import CustomerProfile
from Apps.Administration.auth_utils import assign_user_group

class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    
    phone_regex = RegexValidator(regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")
    phone = forms.CharField(validators=[phone_regex], max_length=10, min_length=10, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Phone Number', 'pattern': '[0-9]{10}', 'title': 'Please enter exactly 10 digits'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add basic form-control class to username and password fields
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'
            # Remove help texts to clean up the UI
            self.fields[field].help_text = ''
                
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Assign user to the 'customer' group
            assign_user_group(user, 'customer')
            
            # Create the CustomerProfile
            CustomerProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', '')
            )
        return user
