from django.urls import path
from . import views


urlpatterns = [
    path('', views.getGoals, name='goals'),
    path('create/', views.GoalCreateView.as_view(), name='createGoal'),
    path('deposit/', views.depositGoalAmount, name='depositGoalAmount'),
]