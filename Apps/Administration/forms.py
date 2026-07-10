from django import forms
from django.contrib.auth.models import User
from Apps.Agent.models import AgentProfile
from Apps.Investor.models import InvestorProfile, Investment, InvestmentListing
from Apps.PublicPage.models import Property
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


class InvestmentForm(forms.ModelForm):
    """Form for creating investments by admin"""
    
    investor = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='investor'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Investor'
    )
    
    property = forms.ModelChoiceField(
        queryset=Property.objects.filter(status='approved'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Property'
    )
    
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter investment amount'}),
        label='Investment Amount'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes'}),
        label='Notes'
    )
    
    class Meta:
        model = Investment
        fields = ['amount', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter investors to only those with investor profiles
        self.fields['investor'].queryset = User.objects.filter(
            groups__name='investor',
            investor_profile__isnull=False
        ).select_related('investor_profile')
        
        # Filter properties to only approved ones with investment listings
        self.fields['property'].queryset = Property.objects.filter(
            status='approved',
            investment_listings__status='active'
        ).distinct().prefetch_related('investment_listings')
    
    def clean(self):
        cleaned_data = super().clean()
        investor = cleaned_data.get('investor')
        property_obj = cleaned_data.get('property')
        amount = cleaned_data.get('amount')
        
        if investor and property_obj and amount:
            # Check if investor already has an investment in this property
            existing_investment = Investment.objects.filter(
                investor=investor,
                listing__property_obj=property_obj
            ).exists()
            
            if existing_investment:
                raise forms.ValidationError(
                    f"{investor.username} already has an investment in this property."
                )
            
            # Check if there's an active investment listing for this property
            try:
                listing = InvestmentListing.objects.get(
                    property_obj=property_obj,
                    status='active'
                )
                
                # Check if amount meets minimum investment
                if amount < listing.minimum_investment:
                    raise forms.ValidationError(
                        f"Minimum investment for this property is ${listing.minimum_investment}"
                    )
                
                # Check if investment would exceed total needed
                total_invested = listing.total_invested_amount
                if total_invested + amount > listing.total_investment_needed:
                    raise forms.ValidationError(
                        f"Investment amount exceeds remaining available funds. "
                        f"Available: ${listing.total_investment_needed - total_invested}"
                    )
                
                # Store the listing for use in save
                cleaned_data['listing'] = listing
                
            except InvestmentListing.DoesNotExist:
                raise forms.ValidationError(
                    "No active investment listing found for this property."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        investment = super().save(commit=False)
        investment.investor = self.cleaned_data['investor']
        investment.listing = self.cleaned_data['listing']
        investment.status = 'confirmed'
        
        if commit:
            investment.save()
        
        return investment
