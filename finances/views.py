from django.shortcuts import render, get_object_or_404
# Create your views here.
import json     
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Transaction, Category, Budget
from django.db.models import Sum

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
    for g in Goal.objects.filter(user=user):
        goals.append({
            "id": str(g.id),
            "name": g.name,
            "target": float(g.target_amount),
            "saved": float(g.saved_amount),
            "deadline": g.deadline.strftime("%Y-%m-%d") if g.deadline else None
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
            data = json.loads(request.body)
            Category.objects.create(
                user=request.user,
                name=data["name"],
                icon=data.get("icon", "default_icon"),
                is_custom=True
            )
            return JsonResponse({"status": "success", "message": "Category created successfully!"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

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
            data = json.loads(request.body)
            category_obj, _ = Category.objects.get_or_create(name=data.get("category", "General"), user=request.user)
            
            Transaction.objects.create(
                user=request.user,
                category=category_obj,
                name=data.get("name", "Untitled"),
                amount=data["amount"],
                type=data["type"], 
                payment_method=data.get("payment_method", "Cash"),
                description=data.get("description", "")
            )
            return JsonResponse({"status": "success", "message": "Transaction added!"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
@login_required
def update_transaction(request, transaction_id):
    """
    Securely update a transaction's details.

    Args:
        request (HttpRequest): The HTTP request containing updated transaction data.
        transaction_id (int): The ID of the transaction to update.

    Returns:
        JsonResponse: Success status or error message.
    """
    if request.method == "POST":
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        data = json.loads(request.body)
        
        transaction.name = data.get("name", transaction.name)
        transaction.amount = data.get("amount", transaction.amount)
        transaction.type = data.get("type", transaction.type)
        transaction.save()
        
        return JsonResponse({"status": "success", "message": "Transaction updated"})
    
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
        transaction.delete()
        return JsonResponse({"status": "success", "message": "Transaction deleted"})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
    

@login_required 
def get_transactions_page(request):
    render("")


@login_required     
def get_reports_page(request):
    render("")


@login_required     
def get_budget_page(request):
    render("")


