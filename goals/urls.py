from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home),

    # Auth
    path('api/login/', views.login_view),
    path('api/signup/', views.signup_view),

    # Dashboard
    path('api/dashboard/', views.dashboard_data),

    # Transactions
    path('api/transactions/add/', views.add_transaction),

    # Goals
    path('api/goals/add/', views.add_goal),
    path('api/goals/deposit/', views.deposit_goal),

    # Categories
    path('api/categories/add/', views.add_category),
    
    path('api/logout/', views.logout_view),
]