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

from django import forms
from Apps.PublicPage.models import PropertyInquiry, Property
from Apps.Agent.models import AgentProfile


class CreatePropertyInquiryForm(forms.ModelForm):
    """
    Form for the 'Connect with a Property Expert' page.
    Sections:
      1. Your Information      -> name, phone_number, email
      2. Select Property Advisor -> agent_profile
      3. Choose a Property     -> related_property (optional, only used if
                                   'I am interested in an available property' is picked)
      4. Your Enquiry          -> subject (mapped into message), message
    """

    # Section 1: Your Information
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        })
    )

    # Section 2: Select Property Advisor
    agent_profile = forms.ModelChoiceField(
        queryset=AgentProfile.objects.select_related('user').all(),
        required=True,
        empty_label="Select an advisor",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_agent_profile'}),
        label="Select Property Advisor",
    )

    # Section 3: Choose a Property
    # Radio choice: existing property vs "looking for another property"
    property_choice = forms.ChoiceField(
        choices=[
            ('existing', 'I am interested in an available property'),
            ('other', 'I am looking for another property'),
        ],
        initial='existing',
        required=True,
        widget=forms.RadioSelect,
        label="Choose a Property",
    )
    related_property = forms.ModelChoiceField(
        queryset=Property.objects.filter(is_active=True),
        required=False,
        empty_label="Select a property",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_related_property'}),
        label="Available Properties",
    )

    # Section 4: Your Enquiry
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter subject (e.g., Need agricultural land near Gorakhpur)',
        })
    )
    message = forms.CharField(
        max_length=1000,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe your requirements in detail...',
            'rows': 5,
            'maxlength': 1000,
            'id': 'id_message',
        })
    )

    class Meta:
        model = PropertyInquiry
        fields = ['name', 'phone_number', 'email', 'agent_profile', 'related_property', 'message']

    def clean(self):
        cleaned_data = super().clean()
        property_choice = cleaned_data.get('property_choice')
        related_property = cleaned_data.get('related_property')

        # If user says they're interested in an existing property, require the property field.
        if property_choice == 'existing' and not related_property:
            self.add_error('related_property', "Please select a property, or choose 'I am looking for another property'.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Prefix the subject into the message body so it's preserved
        # (PropertyInquiry model has no separate subject field).
        subject = self.cleaned_data.get('subject', '').strip()
        message = self.cleaned_data.get('message', '').strip()
        if subject:
            instance.message = f"Subject: {subject}\n\n{message}"
        else:
            instance.message = message

        # If the user picked "I am looking for another property", clear related_property.
        if self.cleaned_data.get('property_choice') == 'other':
            instance.related_property = None

        if commit:
            instance.save()
        return instance