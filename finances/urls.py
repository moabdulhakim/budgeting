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
    path('api/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('api/budgets/set/', views.set_budget, name='set_budget'),
    path('api/transactions/add/', views.add_transaction, name='add_transaction'),
    path('api/transactions/update/<int:transaction_id>/', views.update_transaction, name='update_transaction'),
    path('api/transactions/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),

    path('transactions/', views.get_transactions_page, name='transactions'),
    path('reports/', views.get_reports_page, name='reports'),
    path('budget/', views.get_budget_page, name='budget'),

    # Receipt OCR
    path('receipts/', views.upload_receipt, name='upload_receipt'),
    path('receipts/<int:scan_id>/confirm/', views.confirm_receipt, name='confirm_receipt'),

    # Voice Transaction
    path('api/voice-transaction/', views.voice_transaction, name='voice_transaction'),

    # Currency / FX
    path('api/fx-rates/', views.get_fx_rates, name='get_fx_rates'),
]   

