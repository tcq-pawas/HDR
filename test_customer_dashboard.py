#!/usr/bin/env python
"""
Test customer dashboard access
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

def test_customer_dashboard():
    """Test customer dashboard access"""
    print("🔍 Testing Customer Dashboard Access")
    print("=" * 40)
    
    # Get or create customer user
    customer_user, created = User.objects.get_or_create(
        username='test_customer',
        defaults={'email': 'customer@test.com'}
    )
    if created:
        customer_user.set_password('testpass123')
        customer_user.save()
        assign_user_group(customer_user, 'customer')
        print("✅ Customer user created")
    else:
        print("✅ Using existing customer user")
    
    # Test dashboard access
    client = Client()
    
    # Login
    login_success = client.login(username='test_customer', password='testpass123')
    print(f"🔐 Login success: {login_success}")
    
    # Test customer dashboard
    try:
        response = client.get('/customer/dashboard/', HTTP_HOST='testserver')
        print(f"📊 Customer dashboard status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Customer dashboard accessible!")
        elif response.status_code == 403:
            print("❌ Access forbidden (permission issue)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing customer dashboard: {str(e)}")
    
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
    test_customer_dashboard()
