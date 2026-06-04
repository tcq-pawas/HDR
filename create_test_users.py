#!/usr/bin/env python
"""
Create test users in the actual database for development/testing
Creates admin, investor, customer, and agent users with proper groups and profiles
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from django.contrib.auth.models import User, Group
from Apps.Administration.auth_utils import assign_user_group
from Apps.Administration.models import AdminProfile
from Apps.Customer.models import CustomerProfile
from Apps.Investor.models import InvestorProfile
from Apps.Agent.models import AgentProfile


def create_test_users():
    """Create test users in the actual database"""
    
    # Define test users
    test_users = {
        'admin_test': {
            'email': 'admin@test.com',
            'password': 'testpass123',
            'role': 'admin',
            'first_name': 'Admin',
            'last_name': 'User'
        },
        'investor_test': {
            'email': 'investor@test.com',
            'password': 'testpass123',
            'role': 'investor',
            'first_name': 'Investor',
            'last_name': 'User'
        },
        'customer_test': {
            'email': 'customer@test.com',
            'password': 'testpass123',
            'role': 'customer',
            'first_name': 'Customer',
            'last_name': 'User'
        },
        'agent_test': {
            'email': 'agent@test.com',
            'password': 'testpass123',
            'role': 'agent',
            'first_name': 'Agent',
            'last_name': 'User'
        }
    }
    
    created_users = []
    
    for username, user_data in test_users.items():
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"⚠️  User '{username}' already exists. Skipping.")
            continue
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        
        # Assign to group
        assign_user_group(user, user_data['role'])
        
        # Create profile based on role
        if user_data['role'] == 'admin':
            AdminProfile.objects.get_or_create(user=user)
        elif user_data['role'] == 'investor':
            InvestorProfile.objects.get_or_create(user=user)
        elif user_data['role'] == 'customer':
            CustomerProfile.objects.get_or_create(user=user)
        elif user_data['role'] == 'agent':
            AgentProfile.objects.get_or_create(user=user)
        
        created_users.append(username)
        print(f"✅ Created user: {username} ({user_data['role']})")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created {len(created_users)} new users:")
    for username in created_users:
        print(f"  - {username}")
    
    print("\nTest Credentials:")
    print("  Username: admin_test | Password: testpass123")
    print("  Username: investor_test | Password: testpass123")
    print("  Username: customer_test | Password: testpass123")
    print("  Username: agent_test | Password: testpass123")


if __name__ == '__main__':
    print("Creating test users in actual database...")
    print("=" * 60)
    create_test_users()
