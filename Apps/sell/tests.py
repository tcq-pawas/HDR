from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from Apps.PublicPage.models import Property

class SellAppTests(TestCase):
    def setUp(self):
        # Create users
        self.seller = User.objects.create_user(username='seller1', password='password123')
        self.other_user = User.objects.create_user(username='buyer1', password='password123')
        
        # Create a property listing for seller
        self.property = Property.objects.create(
            title="Seller Villa",
            price=500000,
            location="Miami",
            property_type="sale",
            category="Managed Farmland",
            public_description="Nice public villa",
            description="Luxury interior detailed description",
            bedrooms=4,
            bathrooms=3,
            area_sqft=3500,
            seller=self.seller,
            status='approved'
        )
        
        self.client = Client()

    def test_property_list_requires_login(self):
        response = self.client.get(reverse('sell:property_list'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_property_list_shows_only_seller_properties(self):
        self.client.login(username='seller1', password='password123')
        response = self.client.get(reverse('sell:property_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seller Villa")

    def test_property_create(self):
        self.client.login(username='seller1', password='password123')
        response = self.client.post(reverse('sell:property_create'), {
            'title': 'New Apartment',
            'price': 150000,
            'location': 'New York',
            'property_type': 'rent',
            'category': 'Managed Farmland',
            'public_description': 'New cozy apartment',
            'description': 'Full detailed specs',
            'bedrooms': 2,
            'bathrooms': 1,
            'area_sqft': 1000,
        })
        self.assertEqual(response.status_code, 302)  # Redirects after successful creation
        
        # Verify it defaults to pending
        new_property = Property.objects.get(title='New Apartment')
        self.assertEqual(new_property.status, 'pending')
        self.assertEqual(new_property.seller, self.seller)

    def test_property_update_restricted(self):
        self.client.login(username='buyer1', password='password123')
        response = self.client.get(reverse('sell:property_update', args=[self.property.pk]))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_property_delete(self):
        self.client.login(username='seller1', password='password123')
        response = self.client.post(reverse('sell:property_delete', args=[self.property.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Property.objects.filter(pk=self.property.pk).exists())
