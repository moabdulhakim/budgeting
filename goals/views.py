from django.contrib.auth.decorators import login_required
from django.http import request
from django.http import HttpResponse
from django.shortcuts import render
from .models import Goal

# Create your views here.

@login_required
def getGoals(request):
    goals = Goal.objects.filter(author=request.user)
        
    return render(request, 'myGoals.html', {'goals': goals})