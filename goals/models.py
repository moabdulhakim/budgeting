from django.conf import settings
from django.db import models
import uuid

class Goal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    dueDate = models.DateField(null=True, blank=True)
    target = models.DecimalField(max_digits=20, decimal_places=2)
    current = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    image = models.ImageField(upload_to='goals/%Y/%m/%d/', null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    @property
    def getProgress(self):
        if self.target == 0:
            return 0
        return (self.current / self.target) * 100
    def __str__(self):
        return f"{self.name} - by {self.author.username} - {self.getProgress}%"
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Transaction(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.amount} - {self.category.name}"