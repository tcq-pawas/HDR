from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend which allows users to authenticate using either their
    username or email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
            
        try:
            # Check if the username matches an email or a username
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Try matching phone number across profiles
            user = None
            try:
                from Apps.Agent.models import AgentProfile
                agent_profile = AgentProfile.objects.filter(phone=username).first()
                if agent_profile:
                    user = agent_profile.user
                else:
                    from Apps.Investor.models import InvestorProfile
                    investor_profile = InvestorProfile.objects.filter(phone=username).first()
                    if investor_profile:
                        user = investor_profile.user
                    else:
                        from Apps.Customer.models import CustomerProfile
                        customer_profile = CustomerProfile.objects.filter(phone=username).first()
                        if customer_profile:
                            user = customer_profile.user
            except Exception:
                pass
            
            if user and user.check_password(password):
                return user
                
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # In case multiple users have the same email address, try to login the first active one
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()
            if user and user.check_password(password):
                return user
            return None
