from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
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

    try:
        data = json.loads(request.body)
        goalId = data.get('goalId')
        amount_val = data.get('amount')

        if not goalId or amount_val is None:
            return JsonResponse({'error': 'Missing goalId or amount'}, status=400)

        amount = Decimal(str(amount_val))
        if amount <= 0:
            return JsonResponse({'error': 'Amount must be positive'}, status=400)

        goal = Goal.objects.get(id=goalId, author=request.user)
        goal.current += amount
        goal.save()

        return JsonResponse({
            'success': True,
            'new_current': str(goal.current),
            'goalId': goalId
        })
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid data format'}, status=400)
    except Goal.DoesNotExist:
        return JsonResponse({'error': 'Goal not found'}, status=404)

@login_required
def getGoalDetailApi(request, goalId):
    goal = get_object_or_404(Goal, id=goalId, author=request.user)
    return JsonResponse({
        'id': str(goal.id),
        'name': goal.name,
        'description': goal.description,
        'target': str(goal.target),
        'current': str(goal.current),
        'progress': float(goal.getProgress),
        'image': goal.image.url if goal.image else None
    })