import os
import sys
import django

# Set up Django environment
sys.path.append('c:\\Users\\AJAY\\HDR\\HDR')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from Apps.PublicPage.models import Property
from django.contrib.auth.models import User

# Get the agent_test user
try:
    agent_user = User.objects.get(username='agent_test')
except User.DoesNotExist:
    # If the user doesn't exist, we create them just like in the test file
    agent_user = User.objects.create_user(
        username='agent_test',
        email='agent@test.com',
        password='testpass123'
    )

# Create another sample property
prop, created = Property.objects.get_or_create(
    title="10 Acre Commercial Agriculture Land in Nashik",
    defaults={
        'price': 6500000.00,
        'location': "Nashik, Maharashtra",
        'property_type': 'sale',
        'category': 'Agricultural Land',
        'seller': agent_user,
        'status': 'approved',
        'public_description': "Expansive 10-acre agricultural land suitable for vineyards or cash crops. Excellent highway connectivity and water resources.",
        'description': "Full details about this 10-acre commercial farmland. Perfect for organic farming, vineyard setup, or agro-tourism. Includes a small farmhouse and fencing.",
        'project_size_acre': "10 Acres",
        'water_source': "Canal Water & Borewell",
        'road_access': "Highway Touch",
        'registry_status': "Clear Title",
        'is_active': True,
        'show_to_public': True,
        'assigned_agent': agent_user
    }
)

if created:
    print(f"Successfully created property: {prop.title} by {agent_user.username}")
else:
    print(f"Property already exists: {prop.title}")
