"""
URL routing configuration for the User Accounts application.
Handles signing up new users, logging in to existing accounts, and logging out.
"""
from django.urls import include, path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]