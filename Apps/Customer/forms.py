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
    username = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username (Optional)'}))
    
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
                
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        
        if phone:
            # If no username is provided and phone is used, ensure it's not taken
            if not username and User.objects.filter(username=phone).exists():
                raise forms.ValidationError("An account with this phone number already exists.")
            
            # Also check profiles
            if CustomerProfile.objects.filter(phone=phone).exists():
                raise forms.ValidationError("This phone number is already registered.")
                
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        username = self.cleaned_data.get('username')
        phone = self.cleaned_data.get('phone')
        email = self.cleaned_data.get('email')
        
        if not username:
            user.username = phone if phone else email
        else:
            user.username = username
            
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = email
        
        if commit:
            user.save()
            # Assign user to the 'customer' group
            assign_user_group(user, 'customer')
            
            # Create the CustomerProfile
            CustomerProfile.objects.create(
                user=user,
                phone=phone if phone else ''
            )
        return user
