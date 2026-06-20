from django import forms
from django.contrib.auth.models import User
from Apps.Agent.models import AgentProfile
from Apps.Investor.models import InvestorProfile
from django.core.validators import RegexValidator

class PartnerRegistrationForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('agent', 'Real Estate Agent'),
        ('owner', 'Property Owner'),
    ]
    
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    
    phone_regex = RegexValidator(regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")
    phone = forms.CharField(validators=[phone_regex], max_length=10, min_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Phone Number', 'pattern': '[0-9]{10}', 'title': 'Please enter exactly 10 digits'}))
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise forms.ValidationError("This email is already registered. Please use a different email or login.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Use email as username since we don't have a username field
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.set_unusable_password()
        user.is_active = False # Require admin approval
        
        if commit:
            user.save()
            
            role = self.cleaned_data['role']
            phone = self.cleaned_data['phone']
            
            # Create the respective profile based on role
            if role in ['agent', 'owner']:
                AgentProfile.objects.create(user=user, phone=phone, is_verified=False)
            elif role == 'investor':
                InvestorProfile.objects.create(user=user, phone=phone, verified=False)
                
            from Apps.Administration.auth_utils import assign_user_group
            assign_user_group(user, role)
                
        return user
