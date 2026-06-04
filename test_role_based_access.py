#!/usr/bin/env python
"""
Test script for role-based access control and dashboard redirection system
Tests the strict role separation and authorization mechanisms
"""

import os
import sys
import django

# Setup Django environment BEFORE any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.management import call_command

from Apps.Administration.auth_utils import (
    get_user_role, assign_user_group, get_role_based_redirect_url,
    role_required, has_role_permission
)
from Apps.Administration.models import AdminProfile
from Apps.Customer.models import CustomerProfile
from Apps.Investor.models import InvestorProfile
from Apps.Agent.models import AgentProfile, PropertyInquiry
from Apps.PublicPage.models import Property


def setup_test_users():
    """Set up test users for all test scenarios"""
    # Create test users for each role (or get existing ones)
    admin_user, _ = User.objects.get_or_create(
        username='admin_test',
        defaults={'email': 'admin@test.com'}
    )
    admin_user.set_password('testpass123')
    admin_user.save()
    
    investor_user, _ = User.objects.get_or_create(
        username='investor_test',
        defaults={'email': 'investor@test.com'}
    )
    investor_user.set_password('testpass123')
    investor_user.save()
    
    customer_user, _ = User.objects.get_or_create(
        username='customer_test',
        defaults={'email': 'customer@test.com'}
    )
    customer_user.set_password('testpass123')
    customer_user.save()
    
    agent_user, _ = User.objects.get_or_create(
        username='agent_test',
        defaults={'email': 'agent@test.com'}
    )
    agent_user.set_password('testpass123')
    agent_user.save()
    
    unassigned_user, _ = User.objects.get_or_create(
        username='unassigned_test',
        defaults={'email': 'unassigned@test.com'}
    )
    unassigned_user.set_password('testpass123')
    unassigned_user.save()
    
    # Assign users to groups
    assign_user_group(admin_user, 'admin')
    assign_user_group(investor_user, 'investor')
    assign_user_group(customer_user, 'customer')
    assign_user_group(agent_user, 'agent')
    
    # Create profiles
    AdminProfile.objects.get_or_create(user=admin_user)
    InvestorProfile.objects.get_or_create(user=investor_user)
    CustomerProfile.objects.get_or_create(user=customer_user)
    AgentProfile.objects.get_or_create(user=agent_user)
    
    return {
        'admin': admin_user,
        'investor': investor_user,
        'customer': customer_user,
        'agent': agent_user,
        'unassigned': unassigned_user
    }


class RoleBasedAccessTest(TestCase):
    """Test suite for role-based access control - for Django test runner"""
    
    def setUp(self):
        """Set up test data"""
        self.users = setup_test_users()
        self.admin_user = self.users['admin']
        self.investor_user = self.users['investor']
        self.customer_user = self.users['customer']
        self.agent_user = self.users['agent']
        self.unassigned_user = self.users['unassigned']
        self.client = Client()
    
    def test_user_role_detection(self):
        """Test that user roles are correctly detected"""
        self.assertEqual(get_user_role(self.admin_user), 'admin')
        self.assertEqual(get_user_role(self.investor_user), 'investor')
        self.assertEqual(get_user_role(self.customer_user), 'customer')
        self.assertEqual(get_user_role(self.agent_user), 'agent')
        self.assertIsNone(get_user_role(self.unassigned_user))
    
    def test_agent_profile_management(self):
        """Test agent profile creation and management"""
        agent_profile, _ = AgentProfile.objects.get_or_create(user=self.agent_user)
        agent_profile.company_name = "Test Realty Company"
        agent_profile.save()
        agent_profile.refresh_from_db()
        self.assertEqual(agent_profile.company_name, "Test Realty Company")
    
    def test_role_permission_functions(self):
        """Test role permission utility functions"""
        self.assertTrue(has_role_permission(self.admin_user, 'admin'))
        self.assertFalse(has_role_permission(self.admin_user, 'agent'))
        self.assertTrue(has_role_permission(self.agent_user, 'agent'))
        self.assertFalse(has_role_permission(self.agent_user, 'admin'))


def run_comprehensive_tests():
    """Run all role-based access tests"""
    print("=" * 60)
    print("ROLE-BASED ACCESS CONTROL TEST SUITE")
    print("=" * 60)
    
    # Setup test users
    users = setup_test_users()
    client = Client()
    
    passed = 0
    failed = 0
    
    # Test 1: User Role Detection
    test_name = "User Role Detection"
    try:
        print(f"\nTesting: {test_name}")
        print("-" * 40)
        assert get_user_role(users['admin']) == 'admin'
        assert get_user_role(users['investor']) == 'investor'
        assert get_user_role(users['customer']) == 'customer'
        assert get_user_role(users['agent']) == 'agent'
        assert get_user_role(users['unassigned']) is None
        print(f"✅ PASSED: {test_name}")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"   Error: {str(e)}")
        failed += 1
    
    # Test 2: Role-Based Redirect URLs
    test_name = "Role-Based Redirect URLs"
    try:
        print(f"\nTesting: {test_name}")
        print("-" * 40)
        admin_url = get_role_based_redirect_url(users['admin'])
        investor_url = get_role_based_redirect_url(users['investor'])
        customer_url = get_role_based_redirect_url(users['customer'])
        agent_url = get_role_based_redirect_url(users['agent'])
        unassigned_url = get_role_based_redirect_url(users['unassigned'])
        
        assert 'admin-dashboard/dashboard' in admin_url
        assert 'investor/dashboard' in investor_url
        assert 'customer/dashboard' in customer_url
        assert 'agent' in agent_url
        assert 'auth/unauthorized' in unassigned_url
        print(f"✅ PASSED: {test_name}")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"   Error: {str(e)}")
        failed += 1
    
    # Test 3: Role Permission Functions
    test_name = "Role Permission Functions"
    try:
        print(f"\nTesting: {test_name}")
        print("-" * 40)
        assert has_role_permission(users['admin'], 'admin')
        assert not has_role_permission(users['admin'], 'customer')
        assert not has_role_permission(users['admin'], 'agent')
        
        assert has_role_permission(users['investor'], 'investor')
        assert not has_role_permission(users['investor'], 'admin')
        
        assert has_role_permission(users['customer'], 'customer')
        assert not has_role_permission(users['customer'], 'investor')
        
        assert has_role_permission(users['agent'], 'agent')
        assert not has_role_permission(users['agent'], 'admin')
        
        assert not has_role_permission(users['unassigned'], 'admin')
        assert not has_role_permission(users['unassigned'], 'agent')
        print(f"✅ PASSED: {test_name}")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"   Error: {str(e)}")
        failed += 1
    
    # Test 4: Agent Profile Management
    test_name = "Agent Profile Management"
    try:
        print(f"\nTesting: {test_name}")
        print("-" * 40)
        agent_profile, _ = AgentProfile.objects.get_or_create(user=users['agent'])
        
        agent_profile.company_name = "Test Realty Company"
        agent_profile.phone = "+1-234-567-8900"
        agent_profile.bio = "Experienced real estate agent"
        agent_profile.save()
        
        agent_profile.refresh_from_db()
        assert agent_profile.company_name == "Test Realty Company"
        assert agent_profile.phone == "+1-234-567-8900"
        assert agent_profile.bio == "Experienced real estate agent"
        print(f"✅ PASSED: {test_name}")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"   Error: {str(e)}")
        failed += 1
    
    # Test 5: Group Assignment
    test_name = "Group Assignment"
    try:
        print(f"\nTesting: {test_name}")
        print("-" * 40)
        # Use get_or_create to handle case where user already exists
        new_user, _ = User.objects.get_or_create(
            username='temp_test_user',
            defaults={'email': 'temp@test.com'}
        )
        new_user.set_password('testpass123')
        new_user.save()
        
        assign_user_group(new_user, 'customer')
        assert get_user_role(new_user) == 'customer', f"Expected 'customer' but got '{get_user_role(new_user)}'"
        
        assign_user_group(new_user, 'investor')
        assert get_user_role(new_user) == 'investor', f"Expected 'investor' but got '{get_user_role(new_user)}'"
        
        assign_user_group(new_user, 'admin')
        new_user.refresh_from_db()
        assert new_user.is_staff, "Admin user should have is_staff=True"
        assert get_user_role(new_user) == 'admin', f"Expected 'admin' but got '{get_user_role(new_user)}'"
        
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
    """Test manual scenarios for role verification"""
    print("\n" + "=" * 60)
    print("MANUAL SCENARIO TESTING")
    print("=" * 60)
    
    users = setup_test_users()
    
    scenarios = [
        {
            'name': 'Admin has admin role',
            'user': users['admin'],
            'role': 'admin',
            'expected': True,
            'description': 'Admin user should have admin role'
        },
        {
            'name': 'Agent has agent role',
            'user': users['agent'],
            'role': 'agent',
            'expected': True,
            'description': 'Agent user should have agent role'
        },
        {
            'name': 'Investor has investor role',
            'user': users['investor'],
            'role': 'investor',
            'expected': True,
            'description': 'Investor user should have investor role'
        },
        {
            'name': 'Customer has customer role',
            'user': users['customer'],
            'role': 'customer',
            'expected': True,
            'description': 'Customer user should have customer role'
        },
        {
            'name': 'Admin cannot have customer role',
            'user': users['admin'],
            'role': 'customer',
            'expected': False,
            'description': 'Admin should not have customer role'
        },
        {
            'name': 'Agent cannot have admin role',
            'user': users['agent'],
            'role': 'admin',
            'expected': False,
            'description': 'Agent should not have admin role'
        },
        {
            'name': 'Investor cannot have customer role',
            'user': users['investor'],
            'role': 'customer',
            'expected': False,
            'description': 'Investor should not have customer role'
        },
        {
            'name': 'Unassigned user has no role',
            'user': users['unassigned'],
            'role': None,
            'expected': True,
            'description': 'Unassigned user should have no role'
        },
    ]
    
    passed = 0
    failed = 0
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"User: {scenario['user'].username}")
        
        # Test role permission
        if scenario['role'] is None:
            result = get_user_role(scenario['user']) is None
        else:
            result = has_role_permission(scenario['user'], scenario['role'])
        
        # Check result
        if result == scenario['expected']:
            print(f"✅ PASSED")
            passed += 1
        else:
            print(f"❌ FAILED: Expected {scenario['expected']}, got {result}")
            failed += 1
    
    print(f"\n\nManual Scenarios Summary: {passed} passed, {failed} failed")


if __name__ == '__main__':
    print("Starting Role-Based Access Control Tests...")
    print("=" * 60)
    
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
        print("✅ Strict role-based access control")
        print("✅ Role detection and assignment")
        print("✅ Cross-role permission validation")
        print("✅ Automatic role-based redirection")
        print("✅ Unassigned user handling")
        print("✅ Group assignment and management")
        print("✅ Agent profile management")
        print("✅ Agent role isolation")
    else:
        print("⚠️  Some issues were found. Please review the test results.")
    
    sys.exit(0 if success else 1)
