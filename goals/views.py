from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from decimal import Decimal, InvalidOperation
import json
from .models import Goal

@login_required
def getGoalsApi(request):
    goals = Goal.objects.filter(author=request.user)
    data = []
    for goal in goals:
        data.append({
            'id': str(goal.id),
            'name': goal.name,
            'target': str(goal.target),
            'current': str(goal.current),
            'progress': float(goal.getProgress),
            'dueDate': goal.dueDate
        })
    return JsonResponse({'goals': data}, safe=False)

@login_required
def depositGoalAmount(request):
    if request.method != 'PUT':
        return HttpResponseNotAllowed(['PUT'])

def index(request):
    return HttpResponse("Hello")

def auth_view_signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'auth/signup.html')
def auth_view_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'auth/login.html')
def home(request):
    return render(request, 'dashboard/index.html')

def reports_view(request):
    return render(request, 'reports/index.html')

def goals_view(request):
    goals = Goal.objects.filter(author=request.user)
    return render(request, 'goals/index.html', {'goals': goals})

def budget_view(request):
    return render(request, 'finances/budget.html')

def transactions_view(request):
    return render(request, 'finances/transactions.html')

def add_transaction(request):
    if request.method == 'POST':
        pass
    return redirect('home')

def add_goal(request):
    if request.method == 'POST':
        pass
    return redirect('goals')

def add_category(request):
    if request.method == 'POST':
        pass
    return redirect('budget')