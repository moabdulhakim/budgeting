from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db import IntegrityError        
import goals
from .models import Goal
import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def add_goal(request):
    """
    Creates a new savings goal for the logged-in user.
    
    Args:
        request (HttpRequest): The HTTP request with goal details in JSON.
        
    Returns:
        JsonResponse: Success status.
    """
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
def deposit_goal(request):
    """
    API endpoint to update the current saved amount of a specific goal.
    
    Args:
        request (HttpRequest): Request object with 'goal_id' and 'amount'.
        
    Returns:
        JsonResponse: Success status or error if goal not found.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            goal = Goal.objects.get(id=data["goal_id"], author=request.user)
            goal.current += float(data["amount"])
            goal.save()
            return JsonResponse({"status": "success"})
        except Goal.DoesNotExist:
            return JsonResponse({"message": "Goal not found"}, status=404)
        
