#!/usr/bin/env python
"""
Quick test for role-based authentication system
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from django.contrib.auth.models import User, Group
from Apps.Administration.auth_utils import get_user_role, assign_user_group, get_role_based_redirect_url

def test_basic_functionality():
    """Test basic role-based functionality"""
    print("🔍 Testing Role-Based Authentication System")
    print("=" * 50)
    
    # Create test groups
    admin_group, created = Group.objects.get_or_create(name='admin')
    investor_group, created = Group.objects.get_or_create(name='investor')
    customer_group, created = Group.objects.get_or_create(name='customer')
    print("✅ Groups created/retrieved")
    
    # Create test users
    admin_user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={'email': 'admin@test.com', 'is_staff': True}
    )
    admin_user.set_password('testpass123')
    admin_user.save()
    
    investor_user, created = User.objects.get_or_create(
        username='test_investor',
        defaults={'email': 'investor@test.com'}
    )
    investor_user.set_password('testpass123')
    investor_user.save()
    
    customer_user, created = User.objects.get_or_create(
        username='test_customer',
        defaults={'email': 'customer@test.com'}
    )
    customer_user.set_password('testpass123')
    customer_user.save()
    
    unassigned_user, created = User.objects.get_or_create(
        username='test_unassigned',
        defaults={'email': 'unassigned@test.com'}
    )
    unassigned_user.set_password('testpass123')
    unassigned_user.save()
    
    print("✅ Test users created")
    
    # Assign users to groups
    assign_user_group(admin_user, 'admin')
    assign_user_group(investor_user, 'investor')
    assign_user_group(customer_user, 'customer')
    # unassigned_user remains unassigned
    
    print("✅ Users assigned to groups")
    
    # Test role detection
    admin_role = get_user_role(admin_user)
    investor_role = get_user_role(investor_user)
    customer_role = get_user_role(customer_user)
    unassigned_role = get_user_role(unassigned_user)
    
    print(f"📋 Role Detection Results:")
    print(f"   Admin user role: {admin_role}")
    print(f"   Investor user role: {investor_role}")
    print(f"   Customer user role: {customer_role}")
    print(f"   Unassigned user role: {unassigned_role}")
    
    # Test redirect URLs
    admin_url = get_role_based_redirect_url(admin_user)
    investor_url = get_role_based_redirect_url(investor_user)
    customer_url = get_role_based_redirect_url(customer_user)
    unassigned_url = get_role_based_redirect_url(unassigned_user)
    
    print(f"\n🔄 Redirect URL Results:")
    print(f"   Admin redirect: {admin_url}")
    print(f"   Investor redirect: {investor_url}")
    print(f"   Customer redirect: {customer_url}")
    print(f"   Unassigned redirect: {unassigned_url}")
    
    # Verify results
    assert admin_role == 'admin', f"Expected admin, got {admin_role}"
    assert investor_role == 'investor', f"Expected investor, got {investor_role}"
    assert customer_role == 'customer', f"Expected customer, got {customer_role}"
    assert unassigned_role is None, f"Expected None, got {unassigned_role}"
    
    assert 'admin-dashboard' in admin_url, f"Admin URL should contain admin-dashboard"
    assert 'investor' in investor_url, f"Investor URL should contain investor"
    assert 'customer' in customer_url, f"Customer URL should contain customer"
    assert 'unauthorized' in unassigned_url, f"Unassigned URL should contain unauthorized"
    
    print("\n🎉 All tests passed!")
    print("\n📝 Test Users Created:")
    print("   Username: test_admin, Password: testpass123")
    print("   Username: test_investor, Password: testpass123")
    print("   Username: test_customer, Password: testpass123")
    print("   Username: test_unassigned, Password: testpass123")
    
    print("\n🌐 Access URLs:")
    print("   Dashboard (smart redirect): http://127.0.0.1:8000/dashboard/")
    print("   Admin dashboard: http://127.0.0.1:8000/admin-dashboard/dashboard/")
    print("   Investor dashboard: http://127.0.0.1:8000/investor/dashboard/")
    print("   Customer dashboard: http://127.0.0.1:8000/customer/dashboard/")
    print("   Login: http://127.0.0.1:8000/auth/login/")

if __name__ == '__main__':
    test_basic_functionality()
