from django.utils import timezone
from django.db.models import Sum, Count, Max
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from datetime import timedelta
import calendar
import json

from finances.models import Category, Notification, Transaction

from .mock_data import ensure_user_mock_data


def root_redirect(request):
    """Landing: unauthenticated users go to login; authenticated users go to dashboard."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def _persist_dashboard_notifications(user, today, budget_categories_90, upcoming_tx_rows):
    """Record one notification per budget alert per month; one per upcoming tx per day while active."""
    for cat in budget_categories_90:
        ref = f"budget90:{user.id}:{cat}:{today.year}-{today.month:02d}"
        msg = f"Warning: 90% of {cat} budget used!"
        if not Notification.objects.filter(user=user, reference_key=ref).exists():
            Notification.objects.create(
                user=user,
                message=msg,
                reference_key=ref,
                is_read=False,
                alert_type=Notification.ALERT_BUDGET,
            )

    for row in upcoming_tx_rows:
        t = row["tx"]
        ref = f"upcoming:{user.id}:{t.id}:{today.isoformat()}"
        msg = row["notif_message"]
        if not Notification.objects.filter(user=user, reference_key=ref).exists():
            Notification.objects.create(
                user=user,
                message=msg,
                reference_key=ref,
                is_read=False,
                alert_type=Notification.ALERT_UPCOMING,
            )


@login_required
def getDashboard(request):
    ensure_user_mock_data(request.user)
    now = timezone.now()
    start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0)
    start_of_previous_month = (start_of_current_month - timedelta(days=1)).replace(day=1)
    end_of_previous_month = start_of_current_month - timedelta(seconds=1)

    incomes = Transaction.objects.filter(user=request.user, type="income")
    expenses = Transaction.objects.filter(user=request.user, type="expense")


    total_income = incomes.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

    total_balance = total_income - total_expenses

    monthly_income = incomes.filter(date__gte=start_of_current_month, date__lte=now).aggregate(total=Sum('amount'))['total'] or 0
    monthly_expenses = expenses.filter(date__gte=start_of_current_month, date__lte=now).aggregate(total=Sum('amount'))['total'] or 0

    savings_rate = (monthly_income - monthly_expenses) / monthly_income * 100 if monthly_income else 0

    prev_income = incomes.filter(date__gte=start_of_previous_month, date__lte=end_of_previous_month).aggregate(total=Sum('amount'))['total'] or 0
    prev_expense = expenses.filter(date__gte=start_of_previous_month, date__lte=end_of_previous_month).aggregate(total=Sum('amount'))['total'] or 0

    income_change = (monthly_income - prev_income) / prev_income * 100 if prev_income else 0
    expense_change = (monthly_expenses - prev_expense) / prev_expense * 100 if prev_expense else 0

    balance_change = income_change - expense_change

    if income_change > 0:
        income_change = f"▲ +{income_change:.2f}% vs last month"
    elif income_change < 0:
        income_change = f"▼ {income_change:.2f}% vs last month"
    else:
        income_change = f"= 0% vs last month"
    
    if expense_change > 0:
        expense_change = f"▲ +{expense_change:.2f}% vs last month"
    elif expense_change < 0:
        expense_change = f"▼ {expense_change:.2f}% vs last month"
    else:
        expense_change = ""
    
    if balance_change > 0:
        balance_change = f"▲ +{balance_change:.2f}% vs last month"
    elif balance_change < 0:
        balance_change = f"▼ {balance_change:.2f}% vs last month"
    else:
        balance_change = ""

    prev_savings_rate = (prev_income - prev_expense) / prev_income * 100 if prev_income else 0
    savings_rate_change = savings_rate - prev_savings_rate

    if savings_rate_change > 0:
        savings_rate_change = f"▲ +{savings_rate_change:.2f}% this month"
    elif savings_rate_change < 0:
        savings_rate_change = f"▼ {savings_rate_change:.2f}% this month"
    else:
        savings_rate_change = f"= 0% this month"


    chart_income_data = []
    chart_expenses_data = []
    chart_labels = []

    for i in range(5, -1, -1):
        month_offset = now.month - 1 - i
        target_month = (month_offset % 12) + 1
        target_year = now.year + (month_offset // 12)
        
        start_date = now.replace(year=target_year, month=target_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(target_year, target_month)[1]
        end_date = start_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

        chart_labels.append(start_date.strftime('%b')) 

        month_inc = incomes.filter(date__range=(start_date, end_date)).aggregate(Sum('amount'))['amount__sum'] or 0
        month_exp = expenses.filter(date__range=(start_date, end_date)).aggregate(Sum('amount'))['amount__sum'] or 0

        chart_income_data.append(float(month_inc))
        chart_expenses_data.append(float(month_exp))

    category_expenses = expenses.filter(date__gte=start_of_current_month).values("category__name").annotate(total=Sum('amount')).order_by('-total')

    donut_labels = [item["category__name"] for item in category_expenses]
    donut_values = [float(item["total"]) for item in category_expenses]

    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]

    # ===== Budget Overview (source of truth: Category.budgeted + current-month expense spending) =====
    cats = Category.objects.filter(user=request.user).order_by("name")
    budget_overview = []
    total_budget = 0.0
    total_spent = 0.0
    budget_threshold_alerts = []

    for cat in cats:
        budgeted = float(cat.budgeted or 0)
        spent_sum = (
            Transaction.objects.filter(
                user=request.user,
                category=cat,
                type="expense",
                date__gte=start_of_current_month,
                date__lte=now,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        spent_sum = float(spent_sum)
        pct = (spent_sum / budgeted * 100) if budgeted else 0
        if budgeted > 0 and spent_sum / budgeted >= 0.9:
            budget_threshold_alerts.append(cat.name)
        budget_overview.append(
            {
                "category": cat.name,
                "amount": round(budgeted, 2),
                "spent": round(spent_sum, 2),
                "percent": min(round(pct, 2), 100),
            }
        )
        total_budget += budgeted
        total_spent += spent_sum

    budget_overview = sorted(budget_overview, key=lambda x: x["spent"], reverse=True)[:5]
    remaining_balance = total_budget - total_spent

    today = timezone.localdate()

    # Upcoming: expense + is_upcoming + due_date; alert when 0..10 days until due (inclusive)
    upcoming_bills = []
    upcoming_rows_for_notify = []
    for t in Transaction.objects.filter(
        user=request.user,
        type="expense",
        is_upcoming=True,
        due_date__isnull=False,
    ).order_by("due_date"):
        due = t.due_date
        days_left = (due - today).days
        if 0 <= days_left <= 10:
            due_display = due.strftime("%b %d, %Y")
            upcoming_bills.append(
                {
                    "name": t.name,
                    "amount": float(t.amount),
                    "due_display": due_display,
                    "days_until": days_left,
                }
            )
            upcoming_rows_for_notify.append(
                {
                    "tx": t,
                    "notif_message": (
                        f'Upcoming: "{t.name}" (${float(t.amount):.2f}) due on {due_display}'
                        + (f" (in {days_left} days)" if days_left != 0 else " (today)")
                    ),
                }
            )

    _persist_dashboard_notifications(
        request.user, today, budget_threshold_alerts, upcoming_rows_for_notify
    )

    dashboard_alerts = []
    for cat in budget_threshold_alerts:
        dashboard_alerts.append({"kind": "budget", "category": cat})
    for bill in upcoming_bills:
        dashboard_alerts.append({"kind": "upcoming", **bill})

    # ── Top Detected Subscription (for the Smart Insight banner) ──────────────
    # Find the expense that repeats in the most distinct calendar months.
    # Only the single top result is needed for the one-line alert banner.
    top_row = (
        Transaction.objects
        .filter(user=request.user, type="expense")
        .annotate(month=TruncMonth("date"))
        .values("name", "amount")
        .annotate(month_count=Count("month", distinct=True))
        .filter(month_count__gte=2)
        .order_by("-month_count", "name")
        .first()
    )
    top_subscription = (
        {"name": top_row["name"], "amount": float(top_row["amount"])}
        if top_row else None
    )

    context = {
        'total_balance': float(total_balance),
        'balance_change': balance_change,
        'monthly_income': float(monthly_income),
        'income_change': income_change,
        'monthly_expenses': float(monthly_expenses),
        'expenses_change': expense_change,
        'savings_rate': round(savings_rate, 2),
        'savings_rate_change': savings_rate_change,
        # dashboard budgeting KPIs
        'total_budget': round(total_budget, 2),
        'remaining_balance': round(remaining_balance, 2),
        
        'chart_labels': json.dumps(chart_labels),
        'chart_income_data': json.dumps(chart_income_data),
        'chart_expenses_data': json.dumps(chart_expenses_data),
        
        'donut_labels': json.dumps(donut_labels),
        'donut_values': json.dumps(donut_values),
        
        'recent_transactions': recent_transactions,
        'budget_overview': budget_overview,
        'budget_threshold_alerts': budget_threshold_alerts,
        'upcoming_bills': upcoming_bills,
        'dashboard_alerts': dashboard_alerts,
        'top_subscription': top_subscription,
    }
    
    return render(request, 'dashboard/index.html', context)


@login_required
def getNotifications(request):
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "notifications/index.html", {"notifications": qs})
