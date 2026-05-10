from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from finances.models import Budget, Category, Notification, Transaction
from goals.models import Goal


class FinanceActionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="pass123456",
        )
        self.client.force_login(self.user)

    def test_delete_transaction_post(self):
        cat = Category.objects.create(user=self.user, name="Food", budgeted=100)
        tx = Transaction.objects.create(
            user=self.user,
            category=cat,
            name="Lunch",
            amount=25,
            type="expense",
        )

        response = self.client.post(reverse("delete_transaction", args=[tx.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(id=tx.id).exists())

    def test_delete_category_post(self):
        cat = Category.objects.create(user=self.user, name="Transport", budgeted=200)
        Budget.objects.create(
            user=self.user,
            category=cat,
            amount=200,
            start_date="2026-05-01",
            end_date="2026-05-31",
        )
        Transaction.objects.create(
            user=self.user,
            category=cat,
            name="Taxi",
            amount=30,
            type="expense",
        )

        response = self.client.post(reverse("delete_category", args=[cat.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(id=cat.id).exists())

    def test_reset_account_data_clears_user_records(self):
        cat = Category.objects.create(user=self.user, name="Bills", budgeted=300)
        Transaction.objects.create(
            user=self.user,
            category=cat,
            name="Electricity",
            amount=80,
            type="expense",
        )
        Budget.objects.create(
            user=self.user,
            category=cat,
            amount=300,
            start_date="2026-05-01",
            end_date="2026-05-31",
        )
        Goal.objects.create(author=self.user, name="Car", target=5000, current=300)
        Notification.objects.create(user=self.user, message="test")

        response = self.client.post(reverse("reset_account_data"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Budget.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Category.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Goal.objects.filter(author=self.user).count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 0)
