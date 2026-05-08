"""
URL Routing for the Goals application.

This module defines the URL patterns for the Goals application, mapping each URL to its corresponding view function or class-based view.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.getGoals, name='goals'), # GET
    path('add/', views.add_goal, name='add_goal'), # POST (modal)
    path('<uuid:goal_id>/delete/', views.delete_goal, name='delete_goal'),
    path('create/', views.GoalCreateView.as_view(), name='createGoal'), # GET, POST
    path('deposit/', views.depositGoalAmount, name='depositGoalAmount'), # PUT
    path('api/deposit/', views.depositGoalAmount, name='api_depositGoalAmount'), # compatibility for fetch('/api/goals/deposit/')
    path('<str:goalId>/', views.getGoal, name='getGoal'), # GET
    path('<str:goalId>/update/', views.GoalUpdateView.as_view(), name='updateGoal'), # GET, POST
]
