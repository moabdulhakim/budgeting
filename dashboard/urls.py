from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.getDashboard, name='dashboard'),
    path('notifications/', views.getNotifications, name='notifications'),
]
