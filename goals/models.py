from django.db import models


class Goal(models.Model):
    id = models.UUIDField()
    # userId = models.ForeignKey() # TODO: Connect with user table
    name = models.CharField(max_length=300)
    dueDate = models.DateField()
    target = models.DecimalField(max_digits=20)
    current = models.DecimalField(max_digits=20)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
