from django.urls import path
from . import views


urlpatterns = [
    path('', views.getDashboard, name='dashboard'), # GET
]