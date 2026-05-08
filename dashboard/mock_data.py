from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from finances.models import Category, Transaction
from goals.models import Goal


def ensure_user_mock_data(user) -> None:
    """
    Seed realistic sample data for a user if their DB is empty.
    This makes charts/reports meaningful out-of-the-box.
    """
    has_any = (
        Transaction.objects.filter(user=user).exists()
        or Category.objects.filter(user=user).exists()
        or Goal.objects.filter(author=user).exists()
    )
    if has_any:
        return

    now = timezone.now()
    rng = random.Random(1337)

    categories = [
        ("Salary", 0),
        ("Housing", 1200),
        ("Groceries", 450),
        ("Transport", 220),
        ("Subscriptions", 60),
        ("Dining", 180),
        ("Health", 90),
        ("Entertainment", 120),
    ]

    cat_objs = {}
    for name, budgeted in categories:
        cat = Category.objects.create(
            user=user,
            name=name,
            budgeted=Decimal(str(budgeted)),
            spent=Decimal("0"),
            is_custom=(name not in ("Salary",)),
        )
        cat_objs[name] = cat

    # Goals
    Goal.objects.create(
        author=user,
        name="Emergency Fund",
        target=Decimal("3000"),
        current=Decimal("850"),
        dueDate=(now + timedelta(days=120)).date(),
    )
    Goal.objects.create(
        author=user,
        name="Vacation",
        target=Decimal("2000"),
        current=Decimal("420"),
        dueDate=(now + timedelta(days=200)).date(),
    )

    # Transactions for last ~110 days (includes last month + 3 months trend)
    start = now - timedelta(days=110)
    days = (now.date() - start.date()).days

    def add_tx(dt, name, amount, tx_type, cat_name):
        Transaction.objects.create(
            user=user,
            name=name,
            amount=Decimal(str(amount)),
            type=tx_type,
            category=cat_objs.get(cat_name),
            date=dt,
            payment_method="Card",
        )

    for d in range(days + 1):
        day = start + timedelta(days=d)

        # monthly salary twice-ish
        if day.day in (1, 15) and rng.random() < 0.7:
            add_tx(day, "Salary", rng.randint(1600, 2400), "income", "Salary")

        # recurring spend
        if day.day == 2:
            add_tx(day, "Rent", 1100, "expense", "Housing")
        if day.day in (5, 20):
            add_tx(day, "Internet + Phone", 55, "expense", "Subscriptions")

        # daily-ish expenses
        if rng.random() < 0.55:
            add_tx(day, "Groceries", rng.randint(15, 65), "expense", "Groceries")
        if rng.random() < 0.25:
            add_tx(day, "Transport", rng.randint(5, 25), "expense", "Transport")
        if rng.random() < 0.18:
            add_tx(day, "Dining Out", rng.randint(10, 45), "expense", "Dining")
        if rng.random() < 0.12:
            add_tx(day, "Entertainment", rng.randint(8, 40), "expense", "Entertainment")

