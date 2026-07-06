from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from Apps.PublicPage.models import Property, PropertyInquiry
from Apps.Customer.models import SavedProperty

class BuyAppTests(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(username='buyer1', password='password123')
        
        # Create approved & pending properties
        self.approved_prop = Property.objects.create(
            title="Approved Mansion",
            price=1200000,
            location="Beverly Hills",
            property_type="sale",
            category="Luxury",
            public_description="Beautiful luxury mansion",
            description="Luxury interior detailed description",
            bedrooms=6,
            bathrooms=5,
            area_sqft=8000,
            status='approved'
        )
        
        self.pending_prop = Property.objects.create(
            title="Pending Condo",
            price=250000,
            location="Chicago",
            property_type="rent",
            category="Apartments",
            public_description="Nice public condo",
            description="Detailed description",
            bedrooms=2,
            bathrooms=2,
            area_sqft=1200,
            status='pending'
        )
        
        self.client = Client()

    def test_property_search_shows_only_approved(self):
        response = self.client.get(reverse('buy:property_search'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved Mansion")
        self.assertNotContains(response, "Pending Condo")

    def test_property_search_filters(self):
        # Filter by location
        response = self.client.get(reverse('buy:property_search') + "?location=Beverly")
        self.assertContains(response, "Approved Mansion")
        
        # Filter by location with zero matches
        response = self.client.get(reverse('buy:property_search') + "?location=Texas")
        self.assertNotContains(response, "Approved Mansion")

    def test_save_and_unsave_property(self):
        self.client.login(username='buyer1', password='password123')
        
        # Save property
        response = self.client.get(reverse('buy:save_property', args=[self.approved_prop.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SavedProperty.objects.filter(customer=self.user, property=self.approved_prop).exists())
        
        # Unsave property
        response = self.client.get(reverse('buy:remove_saved_property', args=[self.approved_prop.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavedProperty.objects.filter(customer=self.user, property=self.approved_prop).exists())

    def test_send_inquiry(self):
        response = self.client.post(reverse('buy:send_inquiry', args=[self.approved_prop.pk]), {
            'name': 'John Doe',
            'email': 'john@example.com',
            'message': 'Is this listing still available?'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PropertyInquiry.objects.filter(property=self.approved_prop, email='john@example.com').exists())
