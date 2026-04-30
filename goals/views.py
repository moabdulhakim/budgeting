from django.http import HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.http import request, JsonResponse
from django.shortcuts import render
from decimal import Decimal, InvalidOperation
import json
from .models import Goal


@login_required
def getGoals(request):
    goals = Goal.objects.filter(author=request.user)
        
    return render(request, 'goals/myGoals.html', {'goals': goals})

class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    fields = [
        'name',
        'description',
        'dueDate',
        'target',
        'current'
    ]
    template_name = 'goals/createGoal.html'
    success_url = '/goals'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


@login_required
def depositGoalAmount(request):
    if request.method != 'PUT':
        return HttpResponseNotAllowed(['PUT'])

    data = json.loads(request.body)
    goalId = data.get('goalId')
    amount = data.get('amount')

    if not goalId or not amount:
        return JsonResponse({'error': 'Missing goalId or amount'})

    try:
        amount = Decimal(amount)
    except (InvalidOperation, TypeError):
        return JsonResponse({'error': 'Invalid amount'})

    try:
        goal = Goal.objects.get(id=goalId, author=request.user)
    except Goal.DoesNotExist:
        return JsonResponse({'error': 'Goal not found or access denied'})

    goal.current += amount
    goal.save()

    return JsonResponse({
        'success': True,
        'new_current': str(goal.current),
        'goalId': goalId
    })