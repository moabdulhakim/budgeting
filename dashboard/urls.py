"""
URL routing for the Dashboard application.

This module maps the root dashboard URL to its respective view function.
"""
from django.urls import path
from . import views
urlpatterns = [
    path('dashboard/', views.getDashboard, name='dashboard'),
    path('notifications/', views.getNotifications, name='notifications'),
]
