"""
URL configuration for the finance API.
Defines endpoints for dashboard data, category & budget  management, 
and transaction CRUD operations.
"""
from django.urls import include, path
from . import views
urlpatterns = [
    path('api/dashboard/', views.dashboard_data, name='dashboard_data'),
    path('api/categories/add/', views.add_category, name='add_category'),
    path('api/budgets/set/', views.set_budget, name='set_budget'),
    path('api/transactions/add/', views.add_transaction, name='add_transaction'),
    path('api/transactions/update/<int:transaction_id>/', views.update_transaction, name='update_transaction'),
    path('api/transactions/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
]   

