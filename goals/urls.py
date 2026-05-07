"""
URL Routing for the Goals application.

Defines API endpoints for adding goals and depositing money into them.
"""
from django.urls import path
from . import views
urlpatterns = [
    path('api/goals/add/', views.add_goal, name='add_goal'),
    path('api/goals/deposit/', views.deposit_goal, name='deposit_goal'),
]
