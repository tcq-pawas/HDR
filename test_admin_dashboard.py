#!/usr/bin/env python
"""
Test admin dashboard access
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from Apps.Administration.auth_utils import assign_user_group

def test_admin_dashboard():
    """Test admin dashboard access"""
    print("🔍 Testing Admin Dashboard Access")
    print("=" * 40)
    
    # Get or create admin user
    admin_user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={'email': 'admin@test.com', 'is_staff': True}
    )
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
        assign_user_group(admin_user, 'admin')
        print("✅ Admin user created")
    else:
        print("✅ Using existing admin user")
    
    # Test dashboard access
    client = Client()
    
    # Login
    login_success = client.login(username='test_admin', password='testpass123')
    print(f"🔐 Login success: {login_success}")
    
    # Test admin dashboard
    try:
        response = client.get('/admin-dashboard/dashboard/', HTTP_HOST='testserver')
        print(f"📊 Admin dashboard status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Admin dashboard accessible!")
        elif response.status_code == 403:
            print("❌ Access forbidden (permission issue)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing admin dashboard: {str(e)}")
    
    # Test smart redirect
    try:
        response = client.get('/dashboard/', HTTP_HOST='testserver')
        print(f"🔄 Smart redirect status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Smart redirect working!")
        else:
            print(f"❌ Smart redirect failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error with smart redirect: {str(e)}")

if __name__ == '__main__':
    test_admin_dashboard()
