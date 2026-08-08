from django.test import TestCase, Client
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property
from Apps.Administration.auth_utils import assign_user_group
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
        assign_user_group(self.user, 'agent')
        self.agent_profile = AgentProfile.objects.create(
            user=self.user,
            phone='9999999999'
        )
    
    def test_dashboard_requires_login(self):
        response = self.client.get('/agent/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_displays_stats(self):
        from Apps.Subscriptions.models import SubscriptionPlan, UserSubscription
        plan = SubscriptionPlan.objects.create(name="Test Plan", is_active=True)
        UserSubscription.objects.create(user=self.user, plan=plan, status='active')

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/agent/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)


from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from .validators import validate_image_file, validate_document_file


class FileUploadSecurityTest(TestCase):
    """Test security validation for uploaded files"""

    def test_valid_image_upload(self):
        # 1x1 valid GIF image bytes
        gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        file_obj = SimpleUploadedFile("test.gif", gif_bytes, content_type="image/gif")
        # Allowed extension check for png/jpg/gif
        from .validators import validate_file_upload, ALLOWED_IMAGE_EXTENSIONS
        validate_file_upload(file_obj, allowed_extensions={'.gif'}.union(ALLOWED_IMAGE_EXTENSIONS), max_size_mb=5)

    def test_invalid_html_disguised_as_pdf(self):
        html_bytes = b"<html><script>alert('xss')</script></html>"
        file_obj = SimpleUploadedFile("doc.pdf", html_bytes, content_type="text/html")
        with self.assertRaises(ValidationError):
            validate_document_file(file_obj)

    def test_dangerous_extension_rejection(self):
        html_bytes = b"<html>test</html>"
        file_obj = SimpleUploadedFile("script.html", html_bytes, content_type="text/html")
        with self.assertRaises(ValidationError):
            validate_document_file(file_obj)

