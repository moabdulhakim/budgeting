from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    """
    Model representing a financial category (e.g., Food, Transport, Salary).

    Attributes:
        user (User): The user who created the custom category. Null for global categories.
        name (str): Name of the category.
        icon (str): Icon identifier for UI display.
        is_custom (bool): Flag to distinguish between system and user-defined categories.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    budgeted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    icon = models.CharField(max_length=50, blank=True, null=True)
    is_custom = models.BooleanField(default=False)
    
    def __str__(self):
        """Returns the string representation of the category."""
        return f"{self.name} ({self.user.username if self.user else 'Global'})"

class Budget(models.Model):
    """
    Model representing a budget allocation for a specific category.

    Attributes:
        user (User): The owner of the budget.
        category (Category): The financial category assigned to this budget.
        amount (Decimal): The maximum amount allocated for this budget.
        start_date (DateField): The beginning of the budget period.
        end_date (DateField): The expiration of the budget period.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    alert_threshold = models.IntegerField(default=80) 

    def __str__(self):
        """Returns a string representation showing category and allocated amount."""         
        return f"Budget {self.category.name} - {self.amount}"

class Transaction(models.Model):
    """
    Model representing a financial transaction.

    Attributes:
        user (User): The owner of the transaction.
        category (Category): The financial category assigned to this transaction.
        name (str): A brief title for the transaction.
        amount (Decimal): The monetary value of the transaction.
        type (str): Indicates if it's an 'income' or 'expense'.
        date (DateTime): When the transaction occurred.
        payment_method (str): Method used for the transaction (optional).
        description (str): Additional details about the transaction (optional).
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, default='Untitled')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=[('income', 'Income'), ('expense', 'Expense')])
    date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=50, blank=True, null=True) # From Blueprint
    description = models.TextField(blank=True, null=True)
    is_upcoming = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        """Returns a string representation of the transaction with user, name, and amount.""" 
        return f"{self.user.username} - {self.name} ({self.amount})"


class Notification(models.Model):
    ALERT_GENERAL = "general"
    ALERT_BUDGET = "budget"
    ALERT_UPCOMING = "upcoming"
    ALERT_CHOICES = [
        (ALERT_GENERAL, "General"),
        (ALERT_BUDGET, "Budget"),
        (ALERT_UPCOMING, "Upcoming"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    reference_key = models.CharField(max_length=320, blank=True, db_index=True)
    alert_type = models.CharField(
        max_length=16, choices=ALERT_CHOICES, default=ALERT_GENERAL
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.user.username}"