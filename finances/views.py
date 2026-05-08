from django.shortcuts import render, get_object_or_404, redirect
# Create your views here.
import json     
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
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
def dashboard_data(request):
    """
    Retrieves and aggregates financial data for the dashboard.

    Calculates total balance, income, expenses, and fetches recent 
    transactions and savings goals.

    Returns:
        JsonResponse: A JSON object containing balance, income, expenses, goals, and recent transactions.
    """
    from goals.models import Goal
    user = request.user
    income = Transaction.objects.filter(user=user, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = Transaction.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    goals = []
    # goals.Goal uses author/target/current (not target_amount/saved_amount)
    for g in Goal.objects.filter(author=user):
        goals.append({
            "id": str(g.id),
            "name": g.name,
            "target": float(g.target),
            "saved": float(g.current),
            "deadline": g.dueDate.strftime("%Y-%m-%d") if g.dueDate else None
        })
    recent_transactions = []
    for t in Transaction.objects.filter(user=user).order_by('-date')[:5]:
        recent_transactions.append({
            "id": t.id,
            "name": t.name,
            "amount": float(t.amount),
            "type": t.type,
            "date": t.date.strftime("%b %d, %Y")
        })
    return JsonResponse({
        "total_balance": float(income) - float(expenses),
        "total_income": float(income),
        "total_expenses": float(expenses),
        "goals": goals,
        "recent_transactions": recent_transactions
    })

@csrf_exempt
@login_required
def add_category(request):
    """
    API endpoint to allow users to create custom spending categories.

    Args:
        request (HttpRequest): Request with JSON body (name, icon).

    Returns:
        JsonResponse: Success or error message.
    """
    
    if request.method == "POST":
        try:
            data = _parse_body(request)
            name = (data.get("name") or "").strip()
            budget = data.get("budget") or data.get("budgeted") or 0
            if not name:
                raise ValueError("Category name is required")
            category_id = (data.get("category_id") or "").strip()
            if category_id:
                cat = get_object_or_404(Category, id=category_id, user=request.user)
                cat.name = name
                try:
                    cat.budgeted = budget
                except Exception:
                    pass
                cat.is_custom = True
                cat.save()
                Notification.objects.create(
                    user=request.user, message=f"Category updated: {cat.name}"
                )
                msg_action = "updated"
            else:
                cat, _ = Category.objects.get_or_create(
                    user=request.user, name=name, defaults={"is_custom": True}
                )
                try:
                    cat.budgeted = budget
                except Exception:
                    pass
                cat.is_custom = True
                cat.save()
                Notification.objects.create(
                    user=request.user, message=f"Category added: {cat.name}"
                )
                msg_action = "added"
            if _wants_json(request):
                return JsonResponse({"status": "success", "message": f"Category {msg_action} successfully!"})
            messages.success(request, f"Category {msg_action} successfully.")
            return redirect("budget")
        except Exception as e:
            if _wants_json(request):
                return JsonResponse({"status": "error", "message": str(e)}, status=400)
            messages.error(request, "Failed to save category.")
            return redirect("budget")

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
def set_budget(request):
    """
    Enables users to set or update their budget for a specific category and time period.

    This view handles POST requests containing JSON data. It identifies the category 
    by ID and either creates a new budget record or updates an existing one for the 
    authenticated user.

    Args:
        request (HttpRequest): The HTTP request object containing a JSON body with:
            - category_id (int): The unique ID of the spending category.
            - amount (decimal): The budgeted amount.
            - start_date (date): The start date of the budget cycle.
            - end_date (date): The end date of the budget cycle.

    Returns:
        JsonResponse: A success status on successful update/creation, or an error 
        message if the process fails.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        category_obj = Category.objects.get(id=data["category_id"])
        Budget.objects.update_or_create(
            user=request.user,
            category=category_obj,
            defaults={
                'amount': data["amount"],
                'start_date': data["start_date"],
                'end_date': data["end_date"]
            }
        )
        return JsonResponse({"status": "success"})
    
@csrf_exempt
@login_required
def add_transaction(request):
    """
    API endpoint to record a new financial transaction.
    
    Args:
        request (HttpRequest): JSON with transaction details (name, amount, type, category).
        
    Returns:
        JsonResponse: Confirmation of the created transaction.
    """
    if request.method == "POST":
        try:
            data = _parse_body(request)
            category_name = (data.get("category") or "General").strip() or "General"
            category_obj, _ = Category.objects.get_or_create(name=category_name, user=request.user)

            raw_upcoming = data.get("is_upcoming")
            is_upcoming = str(raw_upcoming).lower() in ("1", "true", "on", "yes", "y")
            due_date = parse_date(data.get("due_date") or "")
            tx_date = parse_date(data.get("tx_date") or data.get("date") or "")
            tx_type = (data.get("type") or "expense").strip() or "expense"
            if is_upcoming and tx_type != "expense":
                msg = "Upcoming alerts apply to expenses only. Change type to Expense or turn off Upcoming."
                if _wants_json(request):
                    return JsonResponse({"status": "error", "message": msg}, status=400)
                messages.error(request, msg)
                return redirect("transactions")
            if not tx_date:
                tx_date = timezone.localdate()
            tx_dt = timezone.make_aware(datetime.combine(tx_date, time(12, 0, 0)))

            if is_upcoming and not due_date:
                msg = "Due date is required for upcoming transactions."
                if _wants_json(request):
                    return JsonResponse({"status": "error", "message": msg}, status=400)
                messages.error(request, msg)
                return redirect("transactions")

            if not is_upcoming:
                due_date = None

            t = Transaction.objects.create(
                user=request.user,
                category=category_obj,
                name=(data.get("name") or "Untitled").strip() or "Untitled",
                amount=data.get("amount") or 0,
                type=tx_type,
                payment_method=data.get("payment_method") or "Cash",
                description=data.get("description") or "",
                date=tx_dt,
                is_upcoming=is_upcoming,
                due_date=due_date,
            )
            Notification.objects.create(
                user=request.user,
                message=f"Transaction added: {t.name} (${float(t.amount):.2f})",
            )
            if _wants_json(request):
                return JsonResponse({"status": "success", "message": "Transaction added!"})
            messages.success(request, "Transaction added successfully.")
            return redirect("transactions")
        except Exception as e:
            if _wants_json(request):
                return JsonResponse({"status": "error", "message": str(e)}, status=400)
            messages.error(request, "Failed to add transaction.")
            return redirect("transactions")

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
@login_required
def delete_transaction(request, transaction_id):
    """
    Removes a transaction from the user's records.

    Args:
        request (HttpRequest): The delete request.
        transaction_id (int): ID of the transaction to delete.

    Returns:
        JsonResponse: Success status of the deletion.
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


