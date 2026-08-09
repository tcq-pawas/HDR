from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator

from Apps.Agent.models import AgentProfile

User = get_user_model()


class InviteAgentForm(forms.Form):
    """Owner invites an agent by email and profile details (no password)."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "agent@example.com",
                "autofocus": True,
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First name"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last name"}
        ),
    )
    phone_regex = RegexValidator(
        regex=r"^\d{10}$",
        message="Phone number must be exactly 10 digits.",
    )
    phone = forms.CharField(
        validators=[phone_regex],
        max_length=10,
        min_length=10,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "10-digit phone number",
                "pattern": "[0-9]{10}",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing = User.objects.filter(email__iexact=email).first()
        if existing and existing.is_active:
            # Allow re-invite only if user is still pending invitation (inactive + pending mapping)
            from .models import AgentOrganizationMapping, AgentInvitation

            has_pending = AgentInvitation.objects.filter(
                agent=existing, status=AgentInvitation.Status.PENDING
            ).exists()
            has_pending_mapping = AgentOrganizationMapping.objects.filter(
                agent=existing,
                status=AgentOrganizationMapping.Status.PENDING_INVITATION,
            ).exists()
            if not (has_pending or has_pending_mapping):
                raise forms.ValidationError(
                    "This email is already associated with an active user account."
                )
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        email = self.cleaned_data.get("email", "").strip().lower()
        qs = AgentProfile.objects.filter(phone=phone)
        if email:
            qs = qs.exclude(user__email__iexact=email)
        if qs.exists():
            raise forms.ValidationError(
                "This phone number is already registered to another account."
            )
        return phone


class CreateAccountFromInvitationForm(forms.Form):
    """Agent completes onboarding via invitation token."""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First name"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last name"}
        ),
    )
    phone_regex = RegexValidator(
        regex=r"^\d{10}$",
        message="Phone number must be exactly 10 digits.",
    )
    phone = forms.CharField(
        validators=[phone_regex],
        max_length=10,
        min_length=10,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "10-digit phone number",
                "pattern": "[0-9]{10}",
            }
        ),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Create a password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm password"}
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        qs = AgentProfile.objects.filter(phone=phone)
        if self.user:
            qs = qs.exclude(user=self.user)
        if qs.exists():
            raise forms.ValidationError(
                "This phone number is already registered to another account."
            )
        return phone

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            validate_password(password1, self.user)
        return password1

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two password fields didn't match.")
        return cleaned
