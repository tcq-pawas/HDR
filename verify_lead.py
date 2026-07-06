import os
import sys
import django

# Set up Django environment
sys.path.append('c:\\Users\\AJAY\\HDR\\HDR')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from Apps.Customer.models import SavedProperty
from Apps.PublicPage.models import Property
from Apps.Agent.models import Lead
from django.contrib.auth.models import User

customer = User.objects.get(username='customer_test')
property_obj = Property.objects.filter(title__icontains="Premium 5 Acre Managed Farmland").first()

# Cleanup first
SavedProperty.objects.filter(customer=customer, property=property_obj).delete()
Lead.objects.filter(agent=property_obj.assigned_agent, email=customer.email).delete()

print("Before save - Lead count:", Lead.objects.filter(agent=property_obj.assigned_agent, email=customer.email).count())

# Simulate saving property
saved, created = SavedProperty.objects.get_or_create(customer=customer, property=property_obj)

print("SavedProperty created?", created)
print("After save - Lead count:", Lead.objects.filter(agent=property_obj.assigned_agent, email=customer.email).count())
