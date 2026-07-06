from django.test import TestCase, Client
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property
from .models import AgentProfile


class AgentDashboardTest(TestCase):
    """Test Agent Dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        from Apps.Administration.auth_utils import assign_user_group
        assign_user_group(self.user, 'agent')
        AgentProfile.objects.get_or_create(user=self.user)
    
    def test_dashboard_requires_login(self):
        response = self.client.get('/agent/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_displays_stats(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/agent/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)
