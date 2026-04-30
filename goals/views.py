from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.http import request
from django.shortcuts import render
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
