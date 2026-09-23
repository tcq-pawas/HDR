from django.test import TestCase, Client
from django.contrib.auth.models import User
from Apps.Administration.auth_utils import assign_user_group
from Apps.Agent.models import AgentProfile
from .models import SubscriptionPlan, PlanPricing, UserSubscription, PaymentTransaction, LedgerEntry


class SubscriptionSecurityTests(TestCase):
    """Tests for subscription security and payment idempotency"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testagent',
            email='agent@example.com',
            password='password123'
        )
        assign_user_group(self.user, 'agent')
        self.agent_profile = AgentProfile.objects.create(
            user=self.user,
            phone='9876543210',
            verification_status='approved'
        )
        
        # Free Plan (Seed)
        self.free_plan = SubscriptionPlan.objects.create(
            name='Seed',
            slug='seed',
            is_active=True
        )
        self.free_pricing = PlanPricing.objects.create(
            plan=self.free_plan,
            billing_cycle='12M',
            price=0.00,
            cashfree_plan_id=''
        )

        # Paid Plan (Harvest)
        self.paid_plan = SubscriptionPlan.objects.create(
            name='Harvest',
            slug='harvest',
            is_active=True
        )
        self.paid_pricing = PlanPricing.objects.create(
            plan=self.paid_plan,
            billing_cycle='1M',
            price=499.00,
            cashfree_plan_id='HARVEST_1M'
        )

    def test_free_checkout_activates_free_plan(self):
        from django.urls import reverse
        self.client.login(username='testagent', password='password123')
        url = reverse('subscriptions:checkout-free', kwargs={'plan_id': self.free_plan.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        sub = UserSubscription.objects.get(user=self.user)
        self.assertEqual(sub.plan, self.free_plan)
        self.assertEqual(sub.status, 'active')

    def test_free_checkout_blocks_paid_plan(self):
        from django.urls import reverse
        self.client.login(username='testagent', password='password123')
        # Attempting to bypass paid plan via free checkout route
        free_url = reverse('subscriptions:checkout-free', kwargs={'plan_id': self.paid_plan.id})
        response = self.client.get(free_url)
        # Should block and redirect to paid checkout
        self.assertEqual(response.status_code, 302)
        paid_url = reverse('subscriptions:checkout-paid', kwargs={'plan_id': self.paid_plan.id})
        self.assertIn(paid_url, response.url)

    def test_ledger_creation_idempotency(self):
        # Create transaction
        tx = PaymentTransaction.objects.create(
            user=self.user,
            order_id='ORDER_TEST_123',
            amount=499.00,
            status='PENDING'
        )
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.paid_plan,
            pricing=self.paid_pricing,
            status='active'
        )
        tx.subscription = sub
        tx.save()

        from .views import _create_ledger_entries_for_subscription

        # First call
        _create_ledger_entries_for_subscription(self.user, tx)
        initial_count = LedgerEntry.objects.filter(payment_transaction=tx).count()
        self.assertEqual(initial_count, 2)  # 1 Credit, 1 Debit

        # Duplicate call (simulating page refresh)
        _create_ledger_entries_for_subscription(self.user, tx)
        final_count = LedgerEntry.objects.filter(payment_transaction=tx).count()
        self.assertEqual(final_count, 2)  # Must remain 2, no duplicates!

