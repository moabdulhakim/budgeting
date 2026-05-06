from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
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

def home(request):
    return render(request, 'dash_collect.html')
