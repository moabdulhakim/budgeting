from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    budgeted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    icon = models.CharField(max_length=50, blank=True, null=True)
    is_custom = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.user.username if self.user else 'Global'})"

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    alert_threshold = models.IntegerField(default=80) 

    def __str__(self):
        return f"Budget {self.category.name} - {self.amount}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, default='Untitled')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=[('income', 'Income'), ('expense', 'Expense')])
    date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=50, blank=True, null=True) # From Blueprint
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.amount})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.user.username}"