"""
finances/urls.py
================
URL routing for the Finances module.

All views use Django's standard render/redirect pattern — no JSON endpoints.

Page views (GET):
    /finances/transactions/          →  get_transactions_page
    /finances/budget/                →  get_budget_page
    /finances/reports/               →  get_reports_page

Form handlers (POST → redirect):
    /finances/transactions/add/      →  add_transaction
    /finances/transactions/delete/<id>/  →  delete_transaction
    /finances/categories/add/        →  add_category
"""

from django.urls import path
from . import views

urlpatterns = [
    path('transactions/',views.get_transactions_page, name='transactions'),
    path('budget/',views.get_budget_page,name='budget'),
    path('reports/',views.get_reports_page,name='reports'),
    path('transactions/add/', views.add_transaction,name='add_transaction'),
    path('transactions/delete/<int:transaction_id>/',views.delete_transaction,name='delete_transaction'),
    path('categories/add/',views.add_category,name='add_category'),
]
