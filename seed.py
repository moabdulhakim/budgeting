from decimal import Decimal
from random import randint, choice, uniform
from django.contrib.auth.models import User
from django.utils import timezone
from finances.models import Transaction, Category, Budget
from datetime import timedelta
import random

user = User.objects.first()

Transaction.objects.filter(user=user).delete()
Budget.objects.filter(user=user).delete()

category_names = [
    "Salary",
    "Freelance",
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Education",
    "Coffee",
    "Subscriptions",
]

categories = {}

for name in category_names:
    cat, _ = Category.objects.get_or_create(
        user=user,
        name=name,
        defaults={
            "icon": "circle",
            "is_custom": True,
            "budgeted": Decimal("0.00"),
            "spent": Decimal("0.00")
        }
    )
    categories[name] = cat

budget_map = {
    "Food": 5000,
    "Transport": 2000,
    "Shopping": 4000,
    "Bills": 3000,
    "Entertainment": 2500,
    "Health": 1500,
    "Education": 2500,
    "Coffee": 1200,
    "Subscriptions": 1000,
}

today = timezone.now().date()

for cat_name, amount in budget_map.items():
    Budget.objects.create(
        user=user,
        category=categories[cat_name],
        amount=Decimal(str(amount)),
        start_date=today - timedelta(days=180),
        end_date=today + timedelta(days=30),
        alert_threshold=80
    )

start_date = timezone.now() - timedelta(days=180)
current_day = start_date

expense_names = {
    "Food": ["McDonalds", "KFC", "Lunch", "Dinner", "Groceries"],
    "Transport": ["Uber", "Metro", "Gas"],
    "Shopping": ["Amazon", "Zara", "Electronics"],
    "Bills": ["Electricity", "Water Bill", "Internet"],
    "Entertainment": ["Cinema", "Netflix Night", "Gaming"],
    "Health": ["Pharmacy", "Doctor"],
    "Education": ["Course", "Books", "Udemy"],
    "Coffee": ["Starbucks", "Cafe"],
    "Subscriptions": ["Netflix", "Spotify", "ChatGPT Plus"],
}

payment_methods = [
    "Cash",
    "Visa",
    "InstaPay",
    "Vodafone Cash"
]

while current_day <= timezone.now():

    if current_day.day in [1, 2]:

        salary = randint(45000, 55000)

        Transaction.objects.create(
            user=user,
            category=categories["Salary"],
            name="Monthly Salary",
            amount=Decimal(str(salary)),
            type="income",
            date=current_day,
            payment_method="Bank Transfer",
            description="Monthly company salary",
        )

        if random.random() > 0.4:

            freelance = randint(4000, 12000)

            Transaction.objects.create(
                user=user,
                category=categories["Freelance"],
                name="Freelance Project",
                amount=Decimal(str(freelance)),
                type="income",
                date=current_day + timedelta(days=10),
                payment_method="InstaPay",
                description="Freelance frontend project",
            )

    tx_count = randint(1, 4)

    for _ in range(tx_count):

        cat_name = choice([
            "Food",
            "Transport",
            "Shopping",
            "Bills",
            "Entertainment",
            "Health",
            "Education",
            "Coffee",
            "Subscriptions",
        ])

        ranges = {
            "Food": (80, 500),
            "Transport": (20, 250),
            "Shopping": (300, 3500),
            "Bills": (400, 1800),
            "Entertainment": (100, 1200),
            "Health": (100, 1400),
            "Education": (300, 2500),
            "Coffee": (40, 180),
            "Subscriptions": (100, 600),
        }

        low, high = ranges[cat_name]

        amount = round(uniform(low, high), 2)

        Transaction.objects.create(
            user=user,
            category=categories[cat_name],
            name=choice(expense_names[cat_name]),
            amount=Decimal(str(amount)),
            type="expense",
            date=current_day + timedelta(
                hours=randint(8, 23),
                minutes=randint(0, 59)
            ),
            payment_method=choice(payment_methods),
            description="Auto generated transaction",
        )

    current_day += timedelta(days=1)

for category in Category.objects.filter(user=user):

    total_spent = Decimal("0.00")

    expenses = Transaction.objects.filter(
        user=user,
        category=category,
        type="expense"
    )

    for tx in expenses:
        total_spent += tx.amount

    category.spent = total_spent

    budget = Budget.objects.filter(
        user=user,
        category=category
    ).first()

    if budget:
        category.budgeted = budget.amount

    category.save()

print("DONE")
print(Transaction.objects.filter(user=user).count())