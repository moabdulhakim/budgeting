"""
URL routing configuration for the User Accounts application.

This module defines the API endpoints for user authentication, including 
signing up new users, logging in to existing accounts, and logging out.
"""
from django.urls import include, path
from . import views

urlpatterns = [
    path('api/signup/', views.signup_view, name='signup'),
    path('api/login/', views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),
]