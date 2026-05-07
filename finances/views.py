"""
finances/views.py
=================
Page views and form-handling views for the Finances module.

All views follow the same render/redirect approach used by the dashboard:
- Page views: compute context → render template
- Form views: process POST → redirect back to the relevant page
No JSON responses are used.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Transaction, Category, Budget
from django.db.models import Sum
from django.utils import timezone
import json
import calendar

@login_required
def get_transactions_page(request):
    """
    Render the Transactions page.

    Fetches all transactions for the user, applies an optional ``filter``
    query parameter (``income`` / ``expenses`` / ``all``), and passes the
    queryset to the template so the correct rows and filter button are shown.

    Args:
        request (HttpRequest): Authenticated GET request.
            Query param ``filter``: ``"income"`` | ``"expenses"`` | ``"all"``

    Returns:
        HttpResponse: Renders ``finances/transactions.html`` with context:
            - **transactions** – filtered, date-sorted QuerySet
            - **active_filter** – the current filter value
            - **categories** – all user categories, for the Add Transaction modal
    """
    active_filter = request.GET.get("filter", "all")

    qs = Transaction.objects.filter(user=request.user).order_by('-date')
    if active_filter == "income":
        qs = qs.filter(type="income")
    elif active_filter == "expenses":
        qs = qs.filter(type="expense")

    categories = Category.objects.filter(user=request.user)

    return render(request, "finances/transactions.html", {
        "transactions":  qs,
        "active_filter": active_filter,
        "categories":    categories,
    })


@login_required
def get_budget_page(request):
    """
    Render the Budget page.

    Computes per-category spending within each budget's date range, derives
    summary stats for the stat cards, and builds JSON-safe strings for the
    Budget vs Actual bar chart canvas data attributes.

    Args:
        request (HttpRequest): Authenticated GET request.

    Returns:
        HttpResponse: Renders ``finances/budget.html`` with context:
            - **budget_categories** – list of dicts:
            ``{name, budget, spent, remaining, percent}``
            - **total_budget**, **total_spent**, **total_remaining** – floats
            - **spent_percent**, **remaining_percent** – ints (0–100)
            - **current_month** – e.g. ``"May 2026"``
            - **budget_chart_labels**, **budget_chart_budgeted**,
              **budget_chart_spent** – JSON strings for the canvas data-attrs
    """
    user  = request.user
    today = timezone.now().date()

    budgets = Budget.objects.filter(user=user).select_related('category')
    budget_categories = []

    for b in budgets:
        spent = float(
            Transaction.objects
            .filter(user=user, category=b.category, type='expense',
                    date__date__gte=b.start_date, date__date__lte=b.end_date)
            .aggregate(Sum('amount'))['amount__sum'] or 0
        )
        budget_amount = float(b.amount)
        remaining = max(budget_amount - spent, 0)
        percent   = min(round((spent / budget_amount * 100) if budget_amount else 0), 100)

        budget_categories.append({
            "name":      b.category.name,
            "budget":    budget_amount,
            "spent":     spent,
            "remaining": remaining,
            "percent":   percent,
        })

    total_budget    = sum(c["budget"] for c in budget_categories)
    total_spent     = sum(c["spent"]  for c in budget_categories)
    total_remaining = max(total_budget - total_spent, 0)
    spent_percent   = min(round((total_spent / total_budget * 100) if total_budget else 0), 100)

    return render(request, "finances/budget.html", {
        "budget_categories":     budget_categories,
        "total_budget":          round(total_budget, 2),
        "total_spent":           round(total_spent, 2),
        "total_remaining":       round(total_remaining, 2),
        "spent_percent":         spent_percent,
        "remaining_percent":     100 - spent_percent,
        "current_month":         today.strftime("%B %Y"),
        "budget_chart_labels":   json.dumps([c["name"]   for c in budget_categories]),
        "budget_chart_budgeted": json.dumps([c["budget"] for c in budget_categories]),
        "budget_chart_spent":    json.dumps([c["spent"]  for c in budget_categories]),
    })


@login_required
def get_reports_page(request):
    """
    Render the Reports page.

    Computes 6-month income/expense trends and a per-category spending
    breakdown for the current month, then passes JSON-safe strings as
    context variables so the template can embed them in canvas data-attrs.

    Args:
        request (HttpRequest): Authenticated GET request.

    Returns:
        HttpResponse: Renders ``reports/index.html`` with context:
            - **monthly_labels**, **monthly_income**, **monthly_expenses**
            – JSON strings for the trend chart
            - **category_labels**, **category_data**
            – JSON strings for the breakdown chart
            - **total_income**, **total_expenses**, **net_balance** – floats
    """
    user = request.user
    now  = timezone.now()

    monthly_labels, monthly_income_data, monthly_expenses_data = [], [], []

    for i in range(5, -1, -1):
        month_offset = now.month - 1 - i
        target_month = (month_offset % 12) + 1
        target_year  = now.year + (month_offset // 12)

        start_date = now.replace(year=target_year, month=target_month, day=1,
                                        hour=0, minute=0, second=0, microsecond=0)
        last_day   = calendar.monthrange(target_year, target_month)[1]
        end_date   = start_date.replace(day=last_day, hour=23, minute=59,
                                        second=59, microsecond=999999)

        monthly_labels.append(start_date.strftime('%b'))
        monthly_income_data.append(float(
            Transaction.objects
            .filter(user=user, type='income', date__range=(start_date, end_date))
            .aggregate(Sum('amount'))['amount__sum'] or 0
        ))
        monthly_expenses_data.append(float(
            Transaction.objects
            .filter(user=user, type='expense', date__range=(start_date, end_date))
            .aggregate(Sum('amount'))['amount__sum'] or 0
        ))

    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cat_spending = (
        Transaction.objects
        .filter(user=user, type='expense', date__gte=start_of_month)
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    category_labels = [row['category__name'] or 'Uncategorised' for row in cat_spending]
    category_data   = [float(row['total']) for row in cat_spending]

    total_income   = float(Transaction.objects.filter(user=user, type='income') .aggregate(Sum('amount'))['amount__sum'] or 0)
    total_expenses = float(Transaction.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0)

    return render(request, "reports/index.html", {
        "monthly_labels":   json.dumps(monthly_labels),
        "monthly_income":   json.dumps(monthly_income_data),
        "monthly_expenses": json.dumps(monthly_expenses_data),
        "category_labels":  json.dumps(category_labels),
        "category_data":    json.dumps(category_data),
        "total_income":     total_income,
        "total_expenses":   total_expenses,
        "net_balance":      total_income - total_expenses,
    })

@require_POST
@login_required
def add_transaction(request):
    """
    Handle the Add Transaction form submission.

    Reads the posted form fields, creates a Transaction, then redirects
    back to the transactions page so the user sees the updated list.

    Args:
        request (HttpRequest): POST with form fields:
            ``name``, ``amount``, ``type``, ``category``

    Returns:
        HttpResponseRedirect: Redirects to ``transactions`` page.
    """
    category_obj, _ = Category.objects.get_or_create(
        name=request.POST.get("category", "General"),
        user=request.user,
    )
    Transaction.objects.create(
        user=request.user,
        category=category_obj,
        name=request.POST.get("name", "Untitled"),
        amount=request.POST["amount"],
        type=request.POST["type"],
        payment_method=request.POST.get("payment_method", "Cash"),
        description=request.POST.get("description", ""),
    )
    return redirect('transactions')


@require_POST
@login_required
def add_category(request):
    """
    Handle the Add Category form submission.

    Creates a new custom Category and, if a budget amount is provided,
    creates a Budget record covering the current calendar month.
    Redirects back to the budget page.

    Args:
        request (HttpRequest): POST with form fields:
            ``name``, ``budget`` (optional monthly amount)

    Returns:
        HttpResponseRedirect: Redirects to ``budget`` page.
    """
    today = timezone.now().date()
    cat = Category.objects.create(
        user=request.user,
        name=request.POST["name"],
        is_custom=True,
    )
    budget_amount = request.POST.get("budget")
    if budget_amount:
        Budget.objects.create(
            user=request.user,
            category=cat,
            amount=budget_amount,
            start_date=today.replace(day=1),
            end_date=today.replace(day=calendar.monthrange(today.year, today.month)[1]),
        )
    return redirect('budget')


@require_POST
@login_required
def delete_transaction(request, transaction_id):
    """
    Delete a transaction owned by the current user.

    Args:
        request (HttpRequest): POST request (no body required).
        transaction_id (int): PK of the transaction to delete.

    Returns:
        HttpResponseRedirect: Redirects to ``transactions`` page.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    return redirect('transactions')
