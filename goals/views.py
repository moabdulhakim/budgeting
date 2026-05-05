from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from decimal import Decimal, InvalidOperation
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum

def home(request):
    return render(request, 'Spendo.html') #[cite: 4]

@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('username')  # Using email as the unique username
            password = data.get('password')
            full_name = data.get('name')

            # 1. Only check if the Email (username) exists
            if User.objects.filter(username=email).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'This email is already registered.'
                }, status=400)

            # 2. Create the user (Name and Password don't need to be unique)
            user = User.objects.create_user(username=email, password=password)
            user.first_name = full_name
            user.save()

            return JsonResponse({
                'status': 'success', 
                'message': 'Account created successfully!',
                'name': full_name
            }, status=201)
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# الدخول
@csrf_exempt
def login_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user = authenticate(username=data["username"], password=data["password"])
        if user:
            login(request, user)
            return JsonResponse({"status": "success", "name": user.username})
        return JsonResponse({"message": "Invalid credentials"}, status=400) #[cite: 4]

@csrf_exempt
def dashboard_data(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    income = Transaction.objects.filter(user=user, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = Transaction.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    # ملاحظة:Expenses مخزنة كأرقام سالبة في الـ JS، تأكد من منطق الحساب
    total_balance = float(income) + float(expenses)

    goals = []
    for g in Goal.objects.filter(author=user):
        goals.append({
            "id": str(g.id),
            "name": g.name,
            "target": float(g.target),
            "saved": float(g.current),
        })

    transactions = []
    for t in Transaction.objects.filter(user=user).order_by('-date'):
        transactions.append({
            "name": t.title,
            "amount": float(t.amount),
            "category": t.category,
            "date": t.date.strftime("%b %d, %Y"),
            "type": t.type
        })
    categories = []
    for c in Category.objects.all():
        categories.append({
            "name": c.name,
            "budgeted": float(c.budgeted),
            "spent": float(c.spent)
        })

    return JsonResponse({
        "total_balance": total_balance,
        "income": float(income),
        "expenses": float(expenses),
        "goals": goals,
        "transactions": transactions,
        "categories": categories,
    })

@csrf_exempt
def add_transaction(request):
    if request.method == "POST":
        data = json.loads(request.body)
        Transaction.objects.create(
            user=request.user,
            title=data["name"], 
            amount=data["amount"],
            category=data["category"],
            type="income" if float(data["amount"]) > 0 else "expense"
        )
        return JsonResponse({"status": "success"}) 

@csrf_exempt
def add_goal(request):
    if request.method == "POST":
        data = json.loads(request.body)
        Goal.objects.create(
            author=request.user,
            name=data["name"],
            target=data["target"],
            current=data.get("saved", 0) 
        )
        return JsonResponse({"status": "success"}) 

@csrf_exempt
def add_category(request):
    if request.method == "POST":
        data = json.loads(request.body)
        Category.objects.create(
            name=data["name"],
            budgeted=data.get("budgeted", 0)
        )
        return JsonResponse({"status": "success"})

@csrf_exempt
def deposit_goal(request):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            goal = Goal.objects.get(id=data["goal_id"], author=request.user)
            goal.current += float(data["amount"])
            goal.save()
            return JsonResponse({"status": "success"})
        except Goal.DoesNotExist:
            return JsonResponse({"message": "Goal not found"}, status=404)
        
@csrf_exempt
def logout_view(request):
    logout(request) #[cite: 4]
    return JsonResponse({"status": "success"})
