from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from finances.models import NotificationPreference, Transaction


class DashboardBehaviorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dash@example.com",
            email="dash@example.com",
            password="pass123456",
        )
        self.client.force_login(self.user)

    def test_dashboard_expenses_count_case_insensitive_types(self):
        Transaction.objects.create(user=self.user, name="Old Expense", amount=50, type="expense")
        # Mixed case from legacy data should still be counted.
        Transaction.objects.create(user=self.user, name="Legacy Expense", amount=30, type="Expense")

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "80")

    def test_toggle_notifications_flips_preference(self):
        self.assertTrue(NotificationPreference.objects.get_or_create(user=self.user)[0].enabled)
        response = self.client.post(reverse("toggle_notifications"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(NotificationPreference.objects.get(user=self.user).enabled)
