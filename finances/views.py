from django.shortcuts import render, get_object_or_404, redirect
# Create your views here.
import json     
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from .models import Transaction, Category, Budget, ReceiptScan
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import datetime, time, timedelta
import calendar
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncDate
from .models import Notification
from django.db import transaction
from .notifications import create_user_notification


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
    income = Transaction.objects.filter(user=user, type__iexact='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = Transaction.objects.filter(user=user, type__iexact='expense').aggregate(Sum('amount'))['amount__sum'] or 0
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
                create_user_notification(request.user, f"Category updated: {cat.name}")
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
                create_user_notification(request.user, f"Category added: {cat.name}")
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
    try:
        cat = get_object_or_404(Category, id=category_id, user=request.user)
        name = cat.name
        cat.delete()
        create_user_notification(request.user, f"Category deleted: {name}")
        if _wants_json(request):
            return JsonResponse({"status": "success", "message": "Category deleted"})
        messages.success(request, "Budget category removed.")
    except Exception as exc:
        if _wants_json(request):
            return JsonResponse({"status": "error", "message": str(exc)}, status=400)
        messages.error(request, "Couldn't delete category.")
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

    Accepts an optional `currency` field (e.g. "EGP"). If provided and
    not "USD", the amount is converted to USD via a live exchange-rate
    API before being stored. The original currency and amount are
    appended to the description for transparency.

    Args:
        request (HttpRequest): JSON or form-encoded transaction details.

    Returns:
        JsonResponse or redirect: Confirmation of the created transaction.
    """
    if request.method == "POST":
        try:
            from .currency import to_usd
            data = _parse_body(request)
            category_name = (data.get("category") or "General").strip() or "General"
            category_obj, _ = Category.objects.get_or_create(name=category_name, user=request.user)

            raw_upcoming = data.get("is_upcoming")
            is_upcoming = str(raw_upcoming).lower() in ("1", "true", "on", "yes", "y")
            due_date = parse_date(data.get("due_date") or "")
            tx_date = parse_date(data.get("tx_date") or data.get("date") or "")
            tx_type = ((data.get("type") or "expense").strip() or "expense").lower()
            if tx_type not in ("income", "expense"):
                tx_type = "expense"
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

            # ── Currency conversion ───────────────────────────────────────────
            raw_amount = Decimal(str(data.get("amount") or 0))
            currency   = (data.get("currency") or "USD").upper().strip()
            usd_amount, rate = to_usd(raw_amount, currency)

            base_description = data.get("description") or ""
            if currency != "USD":
                fx_note = (
                    f"[Originally {raw_amount} {currency}"
                    f" @ {float(rate):.4f} {currency}/USD]"
                )
                description = f"{base_description} {fx_note}".strip()
            else:
                description = base_description

            t = Transaction.objects.create(
                user=request.user,
                category=category_obj,
                name=(data.get("name") or "Untitled").strip() or "Untitled",
                amount=usd_amount,
                type=tx_type,
                payment_method=data.get("payment_method") or "Cash",
                description=description,
                date=tx_dt,
                is_upcoming=is_upcoming,
                due_date=due_date,
            )
            create_user_notification(
                request.user,
                f"Transaction added: {t.name} (${float(t.amount):.2f})",
            )
            if _wants_json(request):
                return JsonResponse({
                    "status": "success",
                    "message": "Transaction added!",
                    "usd_amount": float(usd_amount),
                    "currency": currency,
                    "rate": float(rate),
                })
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

    new_type = ((data.get("type") or transaction.type or "expense").strip() or "expense").lower()
    if new_type not in ("income", "expense"):
        new_type = "expense"
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

    create_user_notification(request.user, f"Transaction updated: {transaction.name}")
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
    if request.method in ("POST", "DELETE"):
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        name = transaction.name
        transaction.delete()
        create_user_notification(request.user, f"Transaction deleted: {name}")
        if _wants_json(request):
            return JsonResponse({"status": "success", "message": "Transaction deleted"})
        messages.success(request, "Transaction deleted successfully.")
        return redirect("transactions")
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@login_required
@require_http_methods(["POST"])
def reset_account_data(request):
    """
    Clear all user-owned finance data and leave account profile intact.
    """
    from goals.models import Goal

    user = request.user
    with transaction.atomic():
        Goal.objects.filter(author=user).delete()
        ReceiptScan.objects.filter(user=user).delete()
        Transaction.objects.filter(user=user).delete()
        Budget.objects.filter(user=user).delete()
        Category.objects.filter(user=user).delete()
        Notification.objects.filter(user=user).delete()

    if _wants_json(request):
        return JsonResponse({"status": "success", "message": "Account data reset successfully"})
    messages.success(request, "All your data has been reset. Start adding your own records.")
    return redirect("dashboard")
    

@login_required 
def get_transactions_page(request):
    user = request.user
    active_filter = request.GET.get("filter", "all")
    qs = Transaction.objects.filter(user=user).select_related("category").order_by("-date")
    if active_filter == "income":
        qs = qs.filter(type__iexact="income")
    elif active_filter == "expenses":
        qs = qs.filter(type__iexact="expense")

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
        tx.filter(type__iexact="expense")
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
    exp_tx = tx.filter(type__iexact="expense")
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
        spent = tx.filter(type__iexact="expense", category=c).aggregate(total=Sum("amount"))["total"] or 0
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
            Transaction.objects.filter(user=user, type__iexact="expense", category=c, date__gte=start)
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


@login_required
@require_http_methods(["GET"])
def get_fx_rates(request):
    """
    Returns the current USD-based exchange rates and the supported currency list.
    Used by the frontend to show a live conversion preview in the transaction modal.

    Returns:
        JsonResponse: { "base": "USD", "rates": {...}, "currencies": {...} }
    """
    from .currency import get_rates, SUPPORTED_CURRENCIES
    return JsonResponse({
        "base": "USD",
        "rates": get_rates(),
        "currencies": SUPPORTED_CURRENCIES,
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def chatbot_reply(request):

    """
    Simple rule-based AI assistant that answers questions about the user's finances.

    Reads real data (transactions, budgets, goals) from the DB and returns
    a plain-text reply based on keyword matching.

    Returns:
        JsonResponse: { "reply": "<string>" }
    """
    from goals.models import Goal

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"reply": "I couldn't understand that. Try again?"}, status=400)

    message = (data.get("message") or "").strip().lower()
    user = request.user

    if not message:
        return JsonResponse({"reply": "Please type something so I can help you! 😊"})

    # ── Fetch user financial data ──────────────────────────────────────────────
    income_total = (
        Transaction.objects.filter(user=user, type__iexact="income")
        .aggregate(Sum("amount"))["amount__sum"] or 0
    )
    expense_total = (
        Transaction.objects.filter(user=user, type__iexact="expense")
        .aggregate(Sum("amount"))["amount__sum"] or 0
    )
    balance = float(income_total) - float(expense_total)

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_income = (
        Transaction.objects.filter(user=user, type__iexact="income", date__gte=month_start)
        .aggregate(Sum("amount"))["amount__sum"] or 0
    )
    monthly_expense = (
        Transaction.objects.filter(user=user, type__iexact="expense", date__gte=month_start)
        .aggregate(Sum("amount"))["amount__sum"] or 0
    )

    goals_qs = Goal.objects.filter(author=user)
    categories_qs = Category.objects.filter(user=user)

    # Top spending category this month
    top_cat = (
        Transaction.objects.filter(user=user, type__iexact="expense", date__gte=month_start)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
        .first()
    )

    # Recent transactions (last 5)
    recent_txs = list(
        Transaction.objects.filter(user=user)
        .order_by("-date")
        .values("name", "amount", "type", "date")[:5]
    )

    # Upcoming bills
    upcoming = list(
        Transaction.objects.filter(user=user, is_upcoming=True, due_date__gte=now.date())
        .order_by("due_date")
        .values("name", "amount", "due_date")[:3]
    )

    # ── Response generation ────────────────────────────────────────────────────
    def fmt(n):
        return f"${float(n):,.2f}"

    reply = None

    # Greetings
    if any(w in message for w in ("hi", "hello", "hey", "howdy", "greetings")):
        reply = (
            f"Hey {user.first_name or user.username}! 👋 I'm Spendo AI, your personal finance assistant. "
            "Ask me about your balance, spending, budgets, goals, or tips!"
        )

    # Balance
    elif any(w in message for w in ("balance", "net worth", "total", "how much do i have")):
        sign = "positive" if balance >= 0 else "negative"
        reply = (
            f"Your current net balance is {fmt(balance)} ({sign}). "
            f"All-time income: {fmt(income_total)} | All-time expenses: {fmt(expense_total)}."
        )

    # Income
    elif any(w in message for w in ("income", "earn", "salary", "revenue", "earned")):
        reply = (
            f"This month you've earned {fmt(monthly_income)}. "
            f"Your all-time total income is {fmt(income_total)}."
        )

    # Spending / expenses
    elif any(w in message for w in ("spend", "spent", "expense", "cost", "paid", "spending")):
        top_info = (
            f" Your top spending category this month is {top_cat['category__name']} ({fmt(top_cat['total'])})."
            if top_cat else ""
        )
        reply = (
            f"This month you've spent {fmt(monthly_expense)}.{top_info} "
            f"All-time expenses total {fmt(expense_total)}."
        )

    # Budget
    elif any(w in message for w in ("budget", "limit", "budgeted", "over budget", "allowance")):
        over_budget = []
        for cat in categories_qs:
            spent = (
                Transaction.objects.filter(user=user, type__iexact="expense", category=cat, date__gte=month_start)
                .aggregate(Sum("amount"))["amount__sum"] or 0
            )
            if cat.budgeted and float(spent) > float(cat.budgeted):
                over_budget.append(f"{cat.name} ({fmt(spent)} / {fmt(cat.budgeted)})")
        if over_budget:
            reply = f"⚠️ You're over budget in: {', '.join(over_budget)}. Consider cutting back in those areas."
        elif categories_qs.exists():
            reply = "Great news — you're within budget across all your categories this month! 🎉"
        else:
            reply = "You haven't set up any budget categories yet. Head to the Budget page to get started!"

    # Goals / savings
    elif any(w in message for w in ("goal", "saving", "savings", "target", "dream", "achieve")):
        if not goals_qs.exists():
            reply = "You haven't created any savings goals yet. Go to Goals to add one!"
        else:
            lines = []
            for g in goals_qs[:4]:
                pct = min(round(float(g.current) / float(g.target) * 100, 1), 100) if g.target else 0
                lines.append(f"• {g.name}: {fmt(g.current)} / {fmt(g.target)} ({pct}%)")
            reply = "Here are your savings goals:\n" + "\n".join(lines)

    # Upcoming / bills
    elif any(w in message for w in ("upcoming", "bill", "bills", "due", "payment", "scheduled")):
        if not upcoming:
            reply = "You have no upcoming bills — you're all clear! "
        else:
            lines = [f"• {u['name']} — {fmt(u['amount'])} due {u['due_date'].strftime('%b %d')}" for u in upcoming]
            reply = "Upcoming payments:\n" + "\n".join(lines)

    # Recent transactions
    elif any(w in message for w in ("recent", "last", "transaction", "latest", "history")):
        if not recent_txs:
            reply = "No transactions found yet. Add some to get started!"
        else:
            lines = []
            for t in recent_txs:
                sign = "+" if t["type"] == "income" else "-"
                lines.append(f"• {t['name']}: {sign}{fmt(t['amount'])} ({t['date'].strftime('%b %d')})")
            reply = "Your 5 most recent transactions:\n" + "\n".join(lines)

    # Tips / advice
    elif any(w in message for w in ("tip", "advice", "suggest", "help", "recommend", "how to save")):
        import random
        tips = [
            "💡 Follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
            "💡 Review your subscriptions — cancel unused ones to free up cash.",
            "💡 Set up automatic savings transfers right after payday.",
            "💡 Track every expense, even small ones — they add up fast.",
            "💡 Build a 3-6 month emergency fund before investing.",
        ]
        reply = random.choice(tips)

    # Fallback
    else:
        reply = (
            "I can help with: balance, income, spending, budgets, "
            "goals, upcoming bills, recent transactions, or saving tips. "
            "What would you like to know? "
        )

    return JsonResponse({"reply": reply})


# ─────────────────────────────────────────────────────────────────────────────
# Receipt OCR
# ─────────────────────────────────────────────────────────────────────────────

def _ocr_parse(image_file):
    """
    Run Tesseract OCR on an uploaded image and extract:
      - raw_text   : full OCR output
      - merchant   : first non-empty line (usually the store name)
      - total      : largest monetary value found in the text
      - receipt_date: first date pattern found

    Returns a dict with those four keys.
    """
    import re
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    img = Image.open(image_file)
    # Upscale small images for better accuracy
    w, h = img.size
    if w < 800:
        scale = 800 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    raw = pytesseract.image_to_string(img, config="--psm 6")

    # ── Merchant ──────────────────────────────────────────────────────────────
    merchant = ""
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and len(stripped) > 2:
            merchant = stripped[:100]
            break

    # ── Total amount ──────────────────────────────────────────────────────────
    # Match patterns like: TOTAL 12.50  /  Total: $12.50  /  Amount: 12.50
    total = None
    total_pattern = re.compile(
        r'(?:total|amount|grand\s*total|subtotal|due|balance)[^\d]*(\d{1,6}[.,]\d{2})',
        re.IGNORECASE,
    )
    matches = total_pattern.findall(raw)
    if matches:
        try:
            total = Decimal(matches[-1].replace(',', '.'))
        except Exception:
            pass
    # Fallback: take the largest dollar figure in the text
    if total is None:
        all_amounts = re.findall(r'\$?\s*(\d{1,6}[.,]\d{2})', raw)
        if all_amounts:
            try:
                total = max(Decimal(a.replace(',', '.')) for a in all_amounts)
            except Exception:
                pass

    # ── Date ─────────────────────────────────────────────────────────────────
    receipt_date = None
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',          # 09/05/2025 or 9-5-25
        r'(\d{4}[/-]\d{2}[/-]\d{2})',                  # 2025-05-09
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',  # 9 May 2025
    ]
    for pat in date_patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            raw_date = m.group(1)
            for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y',
                        '%d %B %Y', '%d %b %Y', '%m/%d/%Y'):
                try:
                    from datetime import datetime as _dt
                    receipt_date = _dt.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue
            if receipt_date:
                break

    return {
        "raw_text":     raw,
        "merchant":     merchant,
        "total":        total,
        "receipt_date": receipt_date,
    }


@login_required
@require_http_methods(["GET", "POST"])
def upload_receipt(request):
    """
    GET  → render the receipt upload page.
    POST → accept an image, run OCR, store a ReceiptScan, redirect to confirm.
    """
    from .models import ReceiptScan

    if request.method == "GET":
        scans = ReceiptScan.objects.filter(user=request.user).order_by("-created_at")[:10]
        return render(request, "finances/receipt_ocr.html", {"scans": scans})

    image = request.FILES.get("receipt_image")
    if not image:
        messages.error(request, "Please choose an image to upload.")
        return redirect("upload_receipt")

    # Basic type check
    if not image.content_type.startswith("image/"):
        messages.error(request, "Only image files are accepted (JPG, PNG, WEBP…).")
        return redirect("upload_receipt")

    scan = ReceiptScan.objects.create(user=request.user, image=image, status=ReceiptScan.STATUS_PENDING)

    try:
        parsed = _ocr_parse(scan.image)
        scan.raw_text     = parsed["raw_text"]
        scan.merchant     = parsed["merchant"]
        scan.total        = parsed["total"]
        scan.receipt_date = parsed["receipt_date"]
        scan.status       = ReceiptScan.STATUS_DONE
        scan.save()
    except Exception as exc:
        scan.status   = ReceiptScan.STATUS_FAILED
        scan.raw_text = str(exc)
        scan.save()
        messages.error(request, f"OCR failed: {exc}")
        return redirect("upload_receipt")

    return redirect("confirm_receipt", scan_id=scan.pk)


@login_required
@require_http_methods(["GET", "POST"])
def confirm_receipt(request, scan_id):
    """
    GET  → show the parsed receipt data in an editable form.
    POST → create a Transaction from the (possibly corrected) data, link it to the scan.
    """
    from .models import ReceiptScan

    scan = get_object_or_404(ReceiptScan, pk=scan_id, user=request.user)
    categories = Category.objects.filter(user=request.user)

    if request.method == "GET":
        return render(request, "finances/receipt_confirm.html", {
            "scan": scan,
            "categories": categories,
        })

    # ── Build the transaction from submitted form data ────────────────────────
    name   = request.POST.get("name", scan.merchant or "Receipt expense").strip() or "Receipt expense"
    amount = request.POST.get("amount", str(scan.total or "0")).strip()
    date   = request.POST.get("date", str(scan.receipt_date or timezone.now().date())).strip()
    cat_id = request.POST.get("category_id", "")
    tx_type = request.POST.get("type", "expense")

    try:
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError
    except Exception:
        messages.error(request, "Please enter a valid positive amount.")
        return render(request, "finances/receipt_confirm.html", {"scan": scan, "categories": categories})

    category = None
    if cat_id:
        try:
            category = Category.objects.get(pk=cat_id, user=request.user)
        except Category.DoesNotExist:
            pass

    from datetime import datetime as _dt
    try:
        tx_date = _dt.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        tx_date = timezone.now().date()

    tx = Transaction.objects.create(
        user=request.user,
        category=category,
        name=name,
        amount=amount,
        type=tx_type,
        date=timezone.make_aware(_dt.combine(tx_date, _dt.min.time())),
    )
    scan.transaction = tx
    scan.save()

    messages.success(request, f' Transaction "{name}" (${amount}) added from receipt!')
    return redirect("transactions")


# ─────────────────────────────────────────────────────────────────────────────
# Voice Transaction
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def voice_transaction(request):
    """
    Parse a natural-language voice transcript and create a Transaction.

    Expected JSON: { "transcript": "spent 45 dollars on groceries" }

    Parsing rules
    - Amount   : first number found in the transcript
    - Type     : 'income' if income keyword present, else 'expense'
    - Name     : text after 'on' / 'for' / 'called'; fallback = cleaned remainder
    - Category : fuzzy-match transcript words against user's category names
    """
    import re

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    transcript = (data.get("transcript") or "").strip()
    if not transcript:
        return JsonResponse({"ok": False, "error": "Empty transcript."})

    text = transcript.lower()

    # Amount
    amount_match = re.search(r'(\d+(?:[.,]\d{1,2})?)', text)
    if not amount_match:
        return JsonResponse({"ok": False, "error": f'No amount found in: "{transcript}"'})
    try:
        amount = Decimal(amount_match.group(1).replace(',', '.'))
    except Exception:
        return JsonResponse({"ok": False, "error": "Could not parse amount."})

    # Type
    income_kw = {"income", "earned", "earn", "received", "receive", "salary",
                 "revenue", "deposited", "got paid"}
    tx_type = "income" if any(kw in text for kw in income_kw) else "expense"

    # Name
    name = ""
    m = re.search(r'\b(?:on|for|called|named)\s+([^,.]+)', text)
    if m:
        name = m.group(1).strip()
    if not name:
        noise = re.sub(
            r'\b(?:spent|spend|paid|pay|bought|buy|added|got|received|earned|'
            r'income|expense|dollars?|dollar|usd|for|on|a|an|the|and|i|my|of)\b',
            ' ', text,
        )
        noise = re.sub(r'\d+(?:[.,]\d{1,2})?', ' ', noise)
        name = ' '.join(noise.split()).title()
    name = (name or "Voice Transaction")[:200]

    # Category – fuzzy match
    category = None
    for cat in Category.objects.filter(user=request.user):
        if cat.name.lower() in text:
            category = cat
            break

    # Create
    tx = Transaction.objects.create(
        user=request.user,
        name=name,
        amount=amount,
        type=tx_type,
        category=category,
        date=timezone.now(),
    )

    return JsonResponse({
        "ok": True,
        "transaction": {
            "id":       tx.pk,
            "name":     tx.name,
            "amount":   float(tx.amount),
            "type":     tx.type,
            "category": category.name if category else None,
        },
    })
