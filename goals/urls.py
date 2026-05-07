"""
URL Routing for the Goals application.

This module defines the URL patterns for the Goals application, mapping each URL to its corresponding view function or class-based view.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.getGoals, name='goals'), # GET
    path('create/', views.GoalCreateView.as_view(), name='createGoal'), # GET, POST
    path('deposit/', views.depositGoalAmount, name='depositGoalAmount'), # PUT
    path('<str:goalId>/', views.getGoal, name='getGoal'), # GET
    path('<str:goalId>/update/', views.GoalUpdateView.as_view(), name='updateGoal'), # GET, POST
]
