"""
finances/views.py
Page views and form-handling views for the Finances module.

All views follow the same render/redirect approach used by the dashboard:
- Page views: compute context → render template
- Form views: process POST → redirect back to the relevant page
No JSON responses are used.
"""
from django.shortcuts import render, get_object_or_404, redirect
# Create your views here.
import json     
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Transaction, Category, Budget
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import datetime, time, timedelta
import calendar
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncDate
from .models import Notification


def _wants_json(request):
    accept = request.headers.get("Accept", "")
    return "application/json" in accept or request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _parse_body(request):
    """
    Accept both JSON requests (fetch) and HTML form submissions (templates).
    """
    ct = (request.headers.get("Content-Type") or "").lower()
    if "application/json" in ct:
        return json.loads(request.body or "{}")
    return request.POST.dict()

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
@require_http_methods(["POST"])
def delete_category(request, category_id):
    cat = get_object_or_404(Category, id=category_id, user=request.user)
    name = cat.name
    cat.delete()
    Notification.objects.create(
        user=request.user, message=f"Category deleted: {name}"
    )
    messages.success(request, "Budget category removed.")
    return redirect("budget")

@csrf_exempt
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




@csrf_exempt
@login_required
def update_transaction(request, transaction_id):
    if request.method != "POST":
        if _wants_json(request):
            return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
        return redirect("transactions")

    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    data = _parse_body(request)

    new_type = (data.get("type") or transaction.type or "expense").strip()
    raw_upcoming = data.get("is_upcoming")
    is_upcoming = str(raw_upcoming).lower() in ("1", "true", "on", "yes", "y")
    due_date = parse_date(data.get("due_date") or "")

    if is_upcoming and new_type != "expense":
        msg = "Upcoming applies to expenses only."
        if _wants_json(request):
            return JsonResponse({"status": "error", "message": msg}, status=400)
        messages.error(request, msg)
        return redirect("transactions")
    if is_upcoming and not due_date:
        msg = "Due date is required for upcoming transactions."
        if _wants_json(request):
            return JsonResponse({"status": "error", "message": msg}, status=400)
        messages.error(request, msg)
        return redirect("transactions")

    if data.get("name") is not None:
        transaction.name = (data.get("name") or "").strip() or transaction.name
    if data.get("amount") is not None:
        try:
            transaction.amount = Decimal(str(data.get("amount")))
        except (InvalidOperation, TypeError, ValueError):
            pass
    transaction.type = new_type

    cat_name = (data.get("category") or "").strip()
    if cat_name:
        co, _ = Category.objects.get_or_create(
            user=request.user, name=cat_name, defaults={"is_custom": True}
        )
        transaction.category = co

    tx_date = parse_date(data.get("tx_date") or data.get("date") or "")
    if tx_date:
        transaction.date = timezone.make_aware(datetime.combine(tx_date, time(12, 0, 0)))

    if not is_upcoming:
        due_date = None
    transaction.is_upcoming = is_upcoming
    transaction.due_date = due_date
    transaction.save()

    Notification.objects.create(
        user=request.user, message=f"Transaction updated: {transaction.name}"
    )
    if _wants_json(request):
        return JsonResponse({"status": "success", "message": "Transaction updated"})
    messages.success(request, "Transaction updated successfully.")
    return redirect("transactions")
    
@csrf_exempt
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
    if request.method == "POST":
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        name = transaction.name
        transaction.delete()
        Notification.objects.create(user=request.user, message=f"Transaction deleted: {name}")
        if _wants_json(request):
            return JsonResponse({"status": "success", "message": "Transaction deleted"})
        messages.success(request, "Transaction deleted successfully.")
        return redirect("transactions")
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
    

@login_required 
def get_transactions_page(request):
    user = request.user
    active_filter = request.GET.get("filter", "all")
    qs = Transaction.objects.filter(user=user).select_related("category").order_by("-date")
    if active_filter == "income":
        qs = qs.filter(type="income")
    elif active_filter == "expenses":
        qs = qs.filter(type="expense")

    transactions = []
    for t in qs:
        transactions.append(
            {
                "id": t.id,
                "name": t.name,
                "amount": float(t.amount),
                "type": t.type,
                "date": t.date.strftime("%b %d, %Y"),
                "date_iso": timezone.localtime(t.date).strftime("%Y-%m-%d"),
                "category": t.category.name if t.category else "Uncategorized",
                "is_upcoming": t.is_upcoming,
                "due_date": t.due_date.strftime("%b %d, %Y") if t.due_date else "",
                "due_iso": t.due_date.isoformat() if t.due_date else "",
                "tx_json": json.dumps(
                    {
                        "id": t.id,
                        "name": t.name,
                        "amount": float(t.amount),
                        "type": t.type,
                        "category": t.category.name if t.category else "Uncategorized",
                        "date_iso": timezone.localtime(t.date).strftime("%Y-%m-%d"),
                        "is_upcoming": t.is_upcoming,
                        "due_iso": t.due_date.isoformat() if t.due_date else "",
                    }
                ),
            }
        )
    return render(
        request,
        "finances/transactions.html",
        {"transactions": transactions, "active_filter": active_filter},
    )


@login_required     
def get_reports_page(request):
    user = request.user
    period = request.GET.get("period", "month")
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "3months":
        # Start at first day of the month two months ago
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        two_months_ago_end = prev_month_start - timedelta(days=1)
        start = two_months_ago_end.replace(day=1)
        end = now
    elif period == "lastmonth":
        # Entire previous calendar month
        prev_month_end = month_start - timedelta(microseconds=1)
        start = (month_start - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = prev_month_end
    else:
        start = month_start
        end = now

    tx = Transaction.objects.filter(user=user, date__gte=start, date__lte=end).select_related("category")

    # Trend (daily buckets across range)
    labels = []
    income_series = []
    expense_series = []
    savings_series = []

    daily = (
        tx.annotate(day=TruncDate("date"))
        .values("day", "type")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )
    daily_map = {}
    for row in daily:
        day = row["day"]
        daily_map.setdefault(day, {"income": 0.0, "expense": 0.0})
        if row["type"] == "income":
            daily_map[day]["income"] += float(row["total"] or 0)
        else:
            daily_map[day]["expense"] += float(row["total"] or 0)

    cur = start.date()
    end_date = end.date()
    while cur <= end_date:
        labels.append(cur.strftime("%b %d"))
        vals = daily_map.get(cur, {"income": 0.0, "expense": 0.0})
        inc = vals["income"]
        exp = vals["expense"]
        income_series.append(round(inc, 2))
        expense_series.append(round(exp, 2))
        savings_series.append(round(inc - exp, 2))
        cur += timedelta(days=1)

    trend_chart_data = json.dumps(
        {"labels": labels, "income": income_series, "expenses": expense_series, "savings": savings_series}
    )

    # Pie (expense breakdown in selected period)
    by_cat = (
        tx.filter(type="expense")
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    pie_labels = [row["category__name"] or "Uncategorized" for row in by_cat]
    pie_values = [float(row["total"] or 0) for row in by_cat]
    pie_chart_data = json.dumps({"labels": pie_labels, "values": pie_values})

    # Weekly spending (bucket the selected range)
    weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
    weekly_values = [0, 0, 0, 0, 0]
    exp_tx = tx.filter(type="expense")
    # If range spans more than one month, bucket by 7-day windows from start
    for t in exp_tx:
        delta_days = (t.date.date() - start.date()).days
        wk = min(max(delta_days // 7, 0), 4)
        weekly_values[wk] += float(t.amount)
    weekly_chart_data = json.dumps({"labels": weeks, "values": weekly_values})

    # Category breakdown table (budgeted vs spent)
    categories = Category.objects.filter(user=user).order_by("name")
    category_breakdown = []
    for c in categories:
        spent = tx.filter(type="expense", category=c).aggregate(total=Sum("amount"))["total"] or 0
        spent = float(spent)
        budgeted = float(c.budgeted or 0)
        remaining = budgeted - spent
        percent = (spent / budgeted * 100) if budgeted else 0
        category_breakdown.append(
            {
                "category": c.name,
                "budgeted": round(budgeted, 2),
                "spent": round(spent, 2),
                "remaining": round(remaining, 2),
                "percent": round(percent, 2),
            }
        )

    return render(
        request,
        "reports/index.html",
        {
            "period": period,
            "trend_chart_data": trend_chart_data,
            "pie_chart_data": pie_chart_data,
            "weekly_chart_data": weekly_chart_data,
            "category_breakdown": category_breakdown,
        },
    )


@login_required     
def get_budget_page(request):
    user = request.user
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    categories = Category.objects.filter(user=user).order_by("name")
    budget_categories = []

    total_budget = 0.0
    total_spent = 0.0

    for c in categories:
        budget = float(c.budgeted or 0)
        spent = (
            Transaction.objects.filter(user=user, type="expense", category=c, date__gte=start)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )
        spent = float(spent)
        remaining = budget - spent
        percent = (spent / budget * 100) if budget else 0
        budget_categories.append(
            {
                "id": c.id,
                "name": c.name,
                "budget": round(budget, 2),
                "spent": round(spent, 2),
                "remaining": round(remaining, 2),
                "percent": min(round(percent, 2), 100),
            }
        )
        total_budget += budget
        total_spent += spent

    total_remaining = total_budget - total_spent
    spent_percent = (total_spent / total_budget * 100) if total_budget else 0
    remaining_percent = 100 - spent_percent if total_budget else 0

    budget_chart_labels = json.dumps([c["name"] for c in budget_categories])
    budget_chart_budgeted = json.dumps([c["budget"] for c in budget_categories])
    budget_chart_spent = json.dumps([c["spent"] for c in budget_categories])

    return render(
        request,
        "finances/budget.html",
        {
            "current_month": now.strftime("%B %Y"),
            "total_budget": round(total_budget, 2),
            "total_spent": round(total_spent, 2),
            "total_remaining": round(total_remaining, 2),
            "spent_percent": round(spent_percent, 2),
            "remaining_percent": round(remaining_percent, 2),
            "budget_categories": budget_categories,
            "budget_chart_labels": budget_chart_labels,
            "budget_chart_budgeted": budget_chart_budgeted,
            "budget_chart_spent": budget_chart_spent,
        },
    )


