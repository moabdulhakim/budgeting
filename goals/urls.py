from django.urls import path
from . import views

urlpatterns = [
    # Goals
    path('api/goals/add/', views.add_goal, name='add_goal'),
    path('api/goals/deposit/', views.deposit_goal, name='deposit_goal'),
]
