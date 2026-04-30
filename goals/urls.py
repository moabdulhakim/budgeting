from django.urls import path
from . import views

urlpatterns = [
    path('api/', views.getGoalsApi, name='api_goals'),
    path('api/deposit/', views.depositGoalAmount, name='api_deposit'),
    path('api/<str:goalId>/', views.getGoalDetailApi, name='api_goal_detail'),
]