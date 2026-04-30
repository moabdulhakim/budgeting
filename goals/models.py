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
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
