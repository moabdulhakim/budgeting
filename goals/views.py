from django.http import HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from decimal import Decimal, InvalidOperation
import json
from .models import Goal
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from finances.notifications import create_user_notification
from django.views.decorators.http import require_http_methods


@login_required
def getGoals(request):
    goals = Goal.objects.filter(author=request.user)

    goals_list = []
    total_saved = 0.0
    total_target = 0.0

    for g in goals.order_by("-createdAt"):
        saved = float(g.current or 0)
        target = float(g.target or 0)
        pct = (saved / target * 100) if target else 0
        completed = bool(target and saved >= target)
        goals_list.append(
            {
                "id": str(g.id),
                "name": g.name,
                "saved": round(saved, 2),
                "target": round(target, 2),
                "percent": min(round(pct, 2), 100),
                "image": g.image,
                "completed": completed,
            }
        )
        total_saved += saved
        total_target += target

    overall_percent = (total_saved / total_target * 100) if total_target else 0

    # Monthly saved (net change in current month)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # If we don't have per-deposit history, approximate by current saved delta in month.
    # For now: show total_saved as "monthly_saved" baseline and 0% change.
    monthly_saved = 0.0
    monthly_saved_change = 0.0

    goals_chart_labels = json.dumps([g["name"] for g in goals_list])
    goals_chart_saved = json.dumps([g["saved"] for g in goals_list])
    goals_chart_targets = json.dumps([g["target"] for g in goals_list])

    celebrate_goal = request.GET.get("celebrate") == "1"

    return render(
        request,
        "goals/index.html",
        {
            "goals": goals_list,
            "goals_count": len(goals_list),
            "total_saved": round(total_saved, 2),
            "total_target": round(total_target, 2),
            "overall_percent": round(overall_percent, 2),
            "monthly_saved": round(monthly_saved, 2),
            "monthly_saved_change": round(monthly_saved_change, 2),
            "goals_chart_labels": goals_chart_labels,
            "goals_chart_saved": goals_chart_saved,
            "goals_chart_targets": goals_chart_targets,
            "celebrate_goal": celebrate_goal,
        },
    )


@login_required
def add_goal(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    goal_id = (request.POST.get("goal_id") or "").strip()
    name = (request.POST.get("name") or "").strip()
    target = request.POST.get("target")
    saved = request.POST.get("saved") or "0"
    image = request.FILES.get("image")

    if not name:
        return redirect("goals")

    try:
        target_val = Decimal(target)
        saved_val = Decimal(saved)
    except (InvalidOperation, TypeError):
        return redirect("goals")

    if goal_id:
        goal = get_object_or_404(Goal, id=goal_id, author=request.user)
        goal.name = name
        goal.target = target_val
        goal.current = saved_val
        if image:
            goal.image = image
        goal.save()
        messages.success(request, "Goal updated successfully.")
        create_user_notification(request.user, f"Goal updated: {goal.name}")
        completed = saved_val >= target_val and target_val > 0
    else:
        goal = Goal.objects.create(
            author=request.user,
            name=name,
            target=target_val,
            current=saved_val,
            image=image,
        )
        messages.success(request, "Goal created successfully.")
        create_user_notification(request.user, f"Goal created: {goal.name}")
        completed = saved_val >= target_val and target_val > 0
    if completed:
        return redirect(f"{reverse('goals')}?celebrate=1")
    return redirect("goals")


@login_required
@require_http_methods(["POST"])
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, author=request.user)
    name = goal.name
    goal.delete()
    create_user_notification(request.user, f"Goal deleted: {name}")
    messages.success(request, "Goal removed.")
    return redirect("goals")


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
    # Support both PUT (API) and POST (simple fetch/form)
    if request.method not in ("PUT", "POST"):
        return HttpResponseNotAllowed(["PUT", "POST"])

    if request.method == "POST" and request.headers.get("Content-Type", "").startswith("application/json"):
        data = json.loads(request.body or "{}")
        goalId = data.get("goalId") or data.get("goal_id")
        amount = data.get("amount")
    elif request.method == "PUT":
        data = json.loads(request.body or "{}")
        goalId = data.get("goalId") or data.get("goal_id")
        amount = data.get("amount")
    else:
        goalId = request.POST.get("goalId") or request.POST.get("goal_id")
        amount = request.POST.get("amount")

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

    celebrate = bool(goal.target and goal.current >= goal.target)

    return JsonResponse({
        'success': True,
        'new_current': str(goal.current),
        'goalId': goalId,
        'celebrate': celebrate,
    })


# get specific goal
@login_required
def getGoal(request, goalId):
    try:
        goal = Goal.objects.get(id=goalId, author=request.user)
    except Goal.DoesNotExist:
        return JsonResponse({'error': 'Goal not found or access denied'})

    return render(request, 'goals/goal.html', {'goal': goal, 'title': goal.name})