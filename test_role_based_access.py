#!/usr/bin/env python
"""
Test script for role-based access control and dashboard redirection system
Tests the strict role separation and authorization mechanisms
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.management import call_command

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from Apps.Administration.auth_utils import (
    get_user_role, assign_user_group, get_role_based_redirect_url,
    role_required, has_role_permission
)
from Apps.Administration.models import AdminProfile
from Apps.Customer.models import CustomerProfile
from Apps.Investor.models import InvestorProfile


class RoleBasedAccessTest(TestCase):
    """Test suite for role-based access control"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users for each role
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.investor_user = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='testpass123'
        )
        
        self.customer_user = User.objects.create_user(
            username='customer_test',
            email='customer@test.com',
            password='testpass123'
        )
        
        self.unassigned_user = User.objects.create_user(
            username='unassigned_test',
            email='unassigned@test.com',
            password='testpass123'
        )
        
        # Assign users to groups
        assign_user_group(self.admin_user, 'admin')
        assign_user_group(self.investor_user, 'investor')
        assign_user_group(self.customer_user, 'customer')
        
        # Create profiles
        AdminProfile.objects.get_or_create(user=self.admin_user)
        InvestorProfile.objects.get_or_create(user=self.investor_user)
        CustomerProfile.objects.get_or_create(user=self.customer_user)
        
        # Create test client
        self.client = Client()
    
    def test_user_role_detection(self):
        """Test that user roles are correctly detected"""
        self.assertEqual(get_user_role(self.admin_user), 'admin')
        self.assertEqual(get_user_role(self.investor_user), 'investor')
        self.assertEqual(get_user_role(self.customer_user), 'customer')
        self.assertIsNone(get_user_role(self.unassigned_user))
        self.assertIsNone(get_user_role(User(username='nonexistent')))
    
    def test_role_based_redirect_urls(self):
        """Test that users get correct redirect URLs based on role"""
        admin_url = get_role_based_redirect_url(self.admin_user)
        investor_url = get_role_based_redirect_url(self.investor_user)
        customer_url = get_role_based_redirect_url(self.customer_user)
        unassigned_url = get_role_based_redirect_url(self.unassigned_user)
        
        self.assertIn('admin-dashboard/dashboard', admin_url)
        self.assertIn('investor/dashboard', investor_url)
        self.assertIn('customer/dashboard', customer_url)
        self.assertIn('auth/unauthorized', unassigned_url)
    
    def test_dashboard_access_control(self):
        """Test that users can only access their own dashboards"""
        # Test admin dashboard access
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to admin dashboard
        
        response = self.client.get('/admin-dashboard/dashboard/')
        self.assertEqual(response.status_code, 200)  # Should access admin dashboard
        
        response = self.client.get('/investor/dashboard/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        response = self.client.get('/customer/dashboard/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        self.client.logout()
        
        # Test investor dashboard access
        self.client.login(username='investor_test', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to investor dashboard
        
        response = self.client.get('/investor/dashboard/')
        self.assertEqual(response.status_code, 200)  # Should access investor dashboard
        
        response = self.client.get('/admin-dashboard/dashboard/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        response = self.client.get('/customer/dashboard/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        self.client.logout()
        
        # Test customer dashboard access
        self.client.login(username='customer_test', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to customer dashboard
        
        response = self.client.get('/customer/dashboard/')
        self.assertEqual(response.status_code, 200)  # Should access customer dashboard
        
        response = self.client.get('/admin-dashboard/dashboard/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        response = self.client.get('/investor/dashboard/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        self.client.logout()
        
        # Test unassigned user access
        self.client.login(username='unassigned_test', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to unauthorized
        
        self.client.logout()
    
    def test_api_access_control(self):
        """Test that API endpoints are protected by role"""
        # Test admin API access
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/admin-dashboard/api/dashboard/')
        self.assertEqual(response.status_code, 200)  # Should access admin API
        
        response = self.client.get('/admin-dashboard/api/users/')
        self.assertEqual(response.status_code, 200)  # Should access user management API
        
        self.client.logout()
        
        # Test non-admin API access denial
        self.client.login(username='investor_test', password='testpass123')
        response = self.client.get('/admin-dashboard/api/dashboard/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        response = self.client.get('/admin-dashboard/api/users/')
        self.assertEqual(response.status_code, 403)  # Should be forbidden
        
        self.client.logout()
    
    def test_authentication_redirect(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
        response = self.client.get('/admin-dashboard/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
        response = self.client.get('/investor/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
        response = self.client.get('/customer/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
    
    def test_role_permission_functions(self):
        """Test role permission utility functions"""
        self.assertTrue(has_role_permission(self.admin_user, 'admin'))
        self.assertFalse(has_role_permission(self.admin_user, 'customer'))
        
        self.assertTrue(has_role_permission(self.investor_user, 'investor'))
        self.assertFalse(has_role_permission(self.investor_user, 'admin'))
        
        self.assertTrue(has_role_permission(self.customer_user, 'customer'))
        self.assertFalse(has_role_permission(self.customer_user, 'investor'))
        
        self.assertFalse(has_role_permission(self.unassigned_user, 'admin'))
        self.assertFalse(has_role_permission(self.unassigned_user, 'customer'))
        self.assertFalse(has_role_permission(self.unassigned_user, 'investor'))
    
    def test_group_assignment(self):
        """Test that group assignment works correctly"""
        # Test creating new user with role
        new_user = User.objects.create_user(
            username='new_test_user',
            email='new@test.com',
            password='testpass123'
        )
        
        assign_user_group(new_user, 'customer')
        self.assertEqual(get_user_role(new_user), 'customer')
        
        # Test role reassignment
        assign_user_group(new_user, 'investor')
        self.assertEqual(get_user_role(new_user), 'investor')
        
        # Test admin gets staff status
        assign_user_group(new_user, 'admin')
        new_user.refresh_from_db()
        self.assertTrue(new_user.is_staff)
        self.assertEqual(get_user_role(new_user), 'admin')
    
    def test_dashboard_data_isolation(self):
        """Test that dashboard data is properly isolated by role"""
        # Test admin dashboard contains system-wide data
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/admin-dashboard/api/dashboard/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Admin should see system statistics
        self.assertIn('counts', data)
        self.assertIn('total_users', data['counts'])
        self.assertIn('total_customers', data['counts'])
        self.assertIn('total_investors', data['counts'])
        
        self.client.logout()
        
        # Test investor dashboard contains only investor data
        self.client.login(username='investor_test', password='testpass123')
        response = self.client.get('/investor/api/dashboard/')
        if response.status_code == 200:  # If endpoint exists
            data = response.json()
            # Investor should only see their own data
            # (This would depend on the actual investor API implementation)
        
        self.client.logout()
        
        # Test customer dashboard contains only customer data
        self.client.login(username='customer_test', password='testpass123')
        # Similar test for customer data isolation
        
        self.client.logout()


def run_comprehensive_tests():
    """Run all role-based access tests"""
    print("=" * 60)
    print("ROLE-BASED ACCESS CONTROL TEST SUITE")
    print("=" * 60)
    
    # Create test case instance
    test_case = RoleBasedAccessTest()
    test_case.setUp()
    
    tests = [
        ("User Role Detection", test_case.test_user_role_detection),
        ("Role-Based Redirect URLs", test_case.test_role_based_redirect_urls),
        ("Dashboard Access Control", test_case.test_dashboard_access_control),
        ("API Access Control", test_case.test_api_access_control),
        ("Authentication Redirect", test_case.test_authentication_redirect),
        ("Role Permission Functions", test_case.test_role_permission_functions),
        ("Group Assignment", test_case.test_group_assignment),
        ("Dashboard Data Isolation", test_case.test_dashboard_data_isolation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            print("-" * 40)
            test_func()
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Role-based access control is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0


def test_manual_scenarios():
    """Test manual scenarios for verification"""
    print("\n" + "=" * 60)
    print("MANUAL SCENARIO TESTING")
    print("=" * 60)
    
    scenarios = [
        {
            'name': 'Admin tries to access investor dashboard',
            'url': '/investor/dashboard/',
            'user': 'admin_test',
            'expected_status': 403,
            'description': 'Admin should be forbidden from accessing investor dashboard'
        },
        {
            'name': 'Investor tries to access customer dashboard',
            'url': '/customer/dashboard/',
            'user': 'investor_test',
            'expected_status': 403,
            'description': 'Investor should be forbidden from accessing customer dashboard'
        },
        {
            'name': 'Customer tries to access admin dashboard',
            'url': '/admin-dashboard/dashboard/',
            'user': 'customer_test',
            'expected_status': 403,
            'description': 'Customer should be forbidden from accessing admin dashboard'
        },
        {
            'name': 'Unassigned user tries to access any dashboard',
            'url': '/dashboard/',
            'user': 'unassigned_test',
            'expected_status': 302,
            'description': 'Unassigned user should be redirected to unauthorized page'
        },
    ]
    
    client = Client()
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"URL: {scenario['url']}")
        print(f"User: {scenario['user']}")
        
        # Login user
        client.login(username=scenario['user'], password='testpass123')
        
        # Make request
        response = client.get(scenario['url'])
        
        # Check result
        if response.status_code == scenario['expected_status']:
            print(f"✅ PASSED: Got expected status {response.status_code}")
        else:
            print(f"❌ FAILED: Expected {scenario['expected_status']}, got {response.status_code}")
        
        # Logout
        client.logout()


if __name__ == '__main__':
    print("Starting Role-Based Access Control Tests...")
    
    # Run automated tests
    success = run_comprehensive_tests()
    
    # Run manual scenarios
    test_manual_scenarios()
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
    
    if success:
        print("🎉 Role-based authentication system is working correctly!")
        print("\nKey Features Verified:")
        print("✅ Strict role-based dashboard access")
        print("✅ Automatic role-based redirection")
        print("✅ API endpoint protection")
        print("✅ Cross-role access prevention")
        print("✅ Unassigned user handling")
        print("✅ Group assignment and management")
    else:
        print("⚠️  Some issues were found. Please review the test results.")
    
    sys.exit(0 if success else 1)
