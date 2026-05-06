from django.urls import path
from . import views

urlpatterns = [
    path('auth/signup/', views.auth_view_signup, name='signup'),
    path('auth/login/', views.auth_view_login, name='login'),
    path('home/', views.home, name='dashboard'),
    path('reports/', views.reports_view, name='reports'),
    path('goals/', views.goals_view, name='goals'),
    path('budget/', views.budget_view, name='budget'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('add-goal/', views.add_goal, name='add_goal'),
    path('add-category/', views.add_category, name='add_category'),
]