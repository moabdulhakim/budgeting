from django.http import HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.http import request, JsonResponse
from django.shortcuts import render
from decimal import Decimal, InvalidOperation
import json
from .models import Goal


@login_required
def getGoals(request):
    goals = Goal.objects.filter(author=request.user)
        
    return render(request, 'goals/myGoals.html', {'goals': goals})

# create goal
class GoalCreateView(LoginRequiredMixin, CreateView):
    """
    Creates a new savings goal for the logged-in user.
    
    Args:
        request (HttpRequest): The HTTP request with goal details in JSON.
        
    Returns:
        JsonResponse: Success status.
    """
    model = Goal
    fields = [
        'name',
        'description',
        'dueDate',
        'target',
        'current',
        'image'
    ]
    template_name = 'goals/createGoal.html'
    success_url = '/goals'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

# update goal
class GoalUpdateView(LoginRequiredMixin, UpdateView):
    model = Goal
    fields = [
        'name',
        'description',
        'dueDate',
        'target',
        'current',
        'image'
    ]
    template_name = 'goals/updateGoal.html'
    success_url = '/goals'
    slug_field = 'id'
    slug_url_kwarg = 'goalId'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

@login_required
def depositGoalAmount(request):
    """
    API endpoint to update the current saved amount of a specific goal.
    
    Args:
        request (HttpRequest): Request object with 'goal_id' and 'amount'.
        
    Returns:
        JsonResponse: Success status or error if goal not found.
    """
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


# get specific goal
@login_required
def getGoal(request, goalId):
    try:
        goal = Goal.objects.get(id=goalId, author=request.user)
    except Goal.DoesNotExist:
        return JsonResponse({'error': 'Goal not found or access denied'})

    return render(request, 'goals/goal.html', {'goal': goal, 'title': goal.name})