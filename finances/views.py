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
    """Allows users to create their own spending categories[cite: 5]."""
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
    """Securely update a transaction's details."""
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
    """Securely delete a transaction belonging to the user."""
    if request.method == "POST":
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        transaction.delete()
        return JsonResponse({"status": "success", "message": "Transaction deleted"})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
    
