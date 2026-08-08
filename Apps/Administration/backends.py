import re

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


def _digits_only(value):
    return re.sub(r'\D', '', str(value or ''))


def _phones_match(stored_phone, login_digits):
    """Match phones by digits only (ignores +91, spaces, dashes)."""
    stored_digits = _digits_only(stored_phone)
    if not stored_digits or not login_digits:
        return False
    if stored_digits == login_digits:
        return True
    if len(stored_digits) >= 10 and len(login_digits) >= 10:
        return stored_digits[-10:] == login_digits[-10:]
    return False


def _find_user_by_profile_phone(login_digits):
    """
    Look up user by mobile number stored on role profiles:
    AgentProfile.phone / alternate_phone,
    CustomerProfile.phone,
    AdminProfile.phone,
    InvestorProfile.phone / phone_number.
    """
    if len(login_digits) < 7:
        return None

    try:
        from Apps.Agent.models import AgentProfile
        for profile in AgentProfile.objects.select_related('user').iterator():
            if _phones_match(profile.phone, login_digits) or _phones_match(
                profile.alternate_phone, login_digits
            ):
                return profile.user
    except Exception:
        pass

    try:
        from Apps.Customer.models import CustomerProfile
        for profile in CustomerProfile.objects.select_related('user').iterator():
            if _phones_match(profile.phone, login_digits):
                return profile.user
    except Exception:
        pass

    try:
        from Apps.Administration.models import AdminProfile
        for profile in AdminProfile.objects.select_related('user').iterator():
            if _phones_match(profile.phone, login_digits):
                return profile.user
    except Exception:
        pass

    try:
        from Apps.Investor.models import InvestorProfile
        for profile in InvestorProfile.objects.select_related('user').iterator():
            if _phones_match(profile.phone, login_digits) or _phones_match(
                profile.phone_number, login_digits
            ):
                return profile.user
    except Exception:
        pass

    return None


def get_user_by_login_identifier(identifier):
    """
    Resolve user by:
      1) username
      2) email (User.email)
      3) mobile number from agent / customer / admin / investor profiles
    """
    if not identifier:
        return None

    identifier = str(identifier).strip()
    if not identifier:
        return None

    # 1) Username
    user = User.objects.filter(username__iexact=identifier).order_by('id').first()
    if user:
        return user

    # 2) Email
    if '@' in identifier:
        user = User.objects.filter(email__iexact=identifier).order_by('id').first()
        if user:
            return user

    # 3) Mobile from profiles
    login_digits = _digits_only(identifier)
    if len(login_digits) < 7:
        return None

    user = _find_user_by_profile_phone(login_digits)
    if user:
        return user

    # Fallback: phone saved as username at registration
    needle = login_digits[-10:] if len(login_digits) >= 10 else login_digits
    return User.objects.filter(
        Q(username=login_digits) | Q(username=needle) | Q(username=identifier)
    ).order_by('id').first()


AUTH_BACKEND_PATH = 'Apps.Administration.backends.EmailOrUsernameModelBackend'


class EmailOrUsernameModelBackend(ModelBackend):
    """Authenticate with username, email, or profile mobile number."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
        if username is None or password is None:
            return None

        user = get_user_by_login_identifier(str(username).strip())
        if user is None:
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
