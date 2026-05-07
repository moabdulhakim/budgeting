from django.shortcuts import redirect
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def signup_view(request):
    """
    Registers a new user by creating a User instance in the database.
    
    Expected POST data: username (email), password, and full name.
    
    Args:
        request (HttpRequest): The HTTP request containing user registration data.
        
    Returns:
        JsonResponse: Success message with status 201 or error message with appropriate status.
    """
    if request.method == "GET":
        return render(request, "auth/signup.html")
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('username')

        if User.objects.filter(email=email).exists():
            return render(request, "auth/signup.html", {'messages': ['This email is already registered.']})

        if User.objects.filter(username=name).exists():
            return render(request, "auth/signup.html", {'messages': ['This username is already taken.']})

        user = User.objects.create_user(username=name, first_name=name, email=email, password=password)
        user.save()

        login(request, user)
        return redirect("dashboard")

@csrf_exempt
def login_view(request):
    """
    Authenticates a user and starts a session.
    
    Args:
        request (HttpRequest): The HTTP request containing login credentials.
        
    Returns:
        JsonResponse: Success status with username or invalid credentials error.
    """
    if request.method == "GET":
        return render(request, "auth/login.html")
        
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(email=email, password=password)
        if user:
            login(request, user)
            return redirect("dashboard") 
            
        return render(request, "auth/login.html", {'messages': ['Invalid credentials']})
    
def logout_view(request):
    """
    Logs out the user and terminates the current session.

    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        JsonResponse: Logout success confirmation.
    """ 
    logout(request)
    return redirect("login")
