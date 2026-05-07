from django.contrib import admin
from finances import models

# Register your models here.
admin.site.register(models.Category) 
admin.site.register(models.Budget) 
admin.site.register(models.Transaction) 
