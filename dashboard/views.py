from django.utils import timezone
from django.db.models import Sum
from finances.models import Budget
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from finances.views import Transaction
from datetime import timedelta
import calendar
import json

@login_required
def getDashboard(request):
    """
    Primary view for the financial dashboard.

    Calculates and aggregates the following metrics:
    - Total Balance: Cumulative income minus expenses.
    - Monthly Performance: Current month's income and expenses vs previous month.
    - Savings Rate: Percentage of income saved.
    - Data Visualizations: Prepares JSON data for income/expense charts and category distribution.
    - Budget Progress: Tracks spending against set budget limits.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'dashboard/index.html' template with a complex 
        context dictionary containing all calculated financial data.
    """
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
        expense_change = f"= 0% vs last month"
    
    if balance_change > 0:
        balance_change = f"▲ +{balance_change:.2f}% vs last month"
    elif balance_change < 0:
        balance_change = f"▼ {balance_change:.2f}% vs last month"
    else:
        balance_change = f"= 0% vs last month"

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
    donut_values = [item["total"] for item in category_expenses]

    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]

    budgets = Budget.objects.filter(user=request.user)

    budget_overview = []

    for budget in budgets:
        spent_sum = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            type='expense',
            date__date__gte=budget.start_date,
            date__date__lte=budget.end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        if budget.amount > 0:
            percent = (spent_sum / budget.amount) * 100
        else:
            percent = 0
            
        budget_overview.append({
            'category': budget.category.name,
            'amount': budget.amount,
            'spent': round(spent_sum, 2),
            'percent': min(round(percent, 2), 100)
        })
    
    context = {
        'total_balance': float(total_balance),
        'balance_change': balance_change,
        'monthly_income': float(monthly_income),
        'income_change': income_change,
        'monthly_expenses': float(monthly_expenses),
        'expenses_change': expense_change,
        'savings_rate': round(savings_rate, 2),
        'savings_rate_change': savings_rate_change,
        
        'chart_labels': json.dumps(chart_labels),
        'chart_income_data': json.dumps(chart_income_data),
        'chart_expenses_data': json.dumps(chart_expenses_data),
        
        'donut_labels': donut_labels,
        'donut_values': donut_values,
        
        'recent_transactions': recent_transactions,
        'budget_overview': budget_overview,
    }
    
    return render(request, 'dashboard/index.html', context)
