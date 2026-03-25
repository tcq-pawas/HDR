#!/usr/bin/env python
"""
Test all dashboards access
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from Apps.Administration.auth_utils import assign_user_group, get_user_role

def test_all_dashboards():
    """Test all dashboard access"""
    print("🔍 Testing All Dashboard Access")
    print("=" * 50)
    
    # Create test users if they don't exist
    users = {
        'admin': ('test_admin', 'admin@test.com', True),
        'investor': ('test_investor', 'investor@test.com', False),
        'customer': ('test_customer', 'customer@test.com', False),
        'unassigned': ('test_unassigned', 'unassigned@test.com', False)
    }
    
    created_users = {}
    
    for role, (username, email, is_staff) in users.items():
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': is_staff}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            if role != 'unassigned':
                assign_user_group(user, role)
            print(f"✅ Created {role} user: {username}")
        else:
            print(f"✅ Using existing {role} user: {username}")
        
        created_users[role] = user
    
    client = Client()
    
    # Test each user's access
    test_cases = [
        ('admin', '/admin-dashboard/dashboard/', 200, 'Admin dashboard'),
        ('admin', '/investor/dashboard/', 403, 'Investor dashboard (should be forbidden)'),
        ('admin', '/customer/dashboard/', 403, 'Customer dashboard (should be forbidden)'),
        
        ('investor', '/investor/dashboard/', 200, 'Investor dashboard'),
        ('investor', '/admin-dashboard/dashboard/', 403, 'Admin dashboard (should be forbidden)'),
        ('investor', '/customer/dashboard/', 403, 'Customer dashboard (should be forbidden)'),
        
        ('customer', '/customer/dashboard/', 200, 'Customer dashboard'),
        ('customer', '/admin-dashboard/dashboard/', 403, 'Admin dashboard (should be forbidden)'),
        ('customer', '/investor/dashboard/', 403, 'Investor dashboard (should be forbidden)'),
        
        ('unassigned', '/dashboard/', 302, 'Smart redirect (should go to unauthorized)'),
    ]
    
    passed = 0
    failed = 0
    
    for role, url, expected_status, description in test_cases:
        user = created_users[role]
        
        # Login
        login_success = client.login(username=user.username, password='testpass123')
        
        if not login_success:
            print(f"❌ Failed to login {role} user")
            failed += 1
            continue
        
        # Test access
        try:
            response = client.get(url, HTTP_HOST='testserver')
            actual_status = response.status_code
            
            if actual_status == expected_status:
                print(f"✅ {description}: {actual_status} ✓")
                passed += 1
            else:
                print(f"❌ {description}: Expected {expected_status}, got {actual_status}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
            failed += 1
        
        # Logout for next test
        client.logout()
    
    # Test smart redirect for each role
    print(f"\n🔄 Testing Smart Redirection")
    print("-" * 30)
    
    redirect_tests = [
        ('admin', '/admin-dashboard/dashboard/'),
        ('investor', '/investor/dashboard/'),
        ('customer', '/customer/dashboard/'),
        ('unassigned', '/auth/unauthorized/'),
    ]
    
    for role, expected_redirect in redirect_tests:
        user = created_users[role]
        
        # Login
        client.login(username=user.username, password='testpass123')
        
        try:
            response = client.get('/dashboard/', HTTP_HOST='testserver', follow=False)
            
            if response.status_code == 302:
                redirect_url = response.url
                if expected_redirect in redirect_url:
                    print(f"✅ {role} smart redirect: {redirect_url} ✓")
                    passed += 1
                else:
                    print(f"❌ {role} smart redirect: Expected {expected_redirect}, got {redirect_url}")
                    failed += 1
            else:
                print(f"❌ {role} smart redirect: Expected 302, got {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {role} smart redirect: Error - {str(e)}")
            failed += 1
        
        client.logout()
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Role-based access control is working perfectly!")
        print("\n📝 Test Users Ready:")
        for role, (username, _, _) in users.items():
            print(f"   {role.title()}: {username} / testpass123")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0

if __name__ == '__main__':
    test_all_dashboards()
