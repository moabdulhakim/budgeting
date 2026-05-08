from django.shortcuts import redirect
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages


def _is_json(request):
    ct = (request.headers.get("Content-Type") or "").lower()
    return "application/json" in ct


def _body_or_post(request):
    if _is_json(request):
        return json.loads(request.body or "{}")
    return request.POST.dict()

# Create your views here.
@csrf_exempt
def signup_view(request):
    if request.method == "GET":
        return render(request, "auth/signup.html")
    """
    Registers a new user by creating a User instance in the database.
    
    Expected POST data: username (email), password, and full name.
    
    Args:
        request (HttpRequest): The HTTP request containing user registration data.
        
    Returns:
        JsonResponse: Success message with status 201 or error message with appropriate status.
    """
    if request.method == 'POST':
        try:
            data = _body_or_post(request)
            email = (data.get('username') or data.get('email') or "").strip()
            password = data.get('password')
            full_name = (data.get('name') or data.get('full_name') or "").strip()

            if User.objects.filter(username=email).exists():
                msg = 'This email is already registered.'
                if _is_json(request):
                    return JsonResponse({'status': 'error', 'message': msg}, status=400)
                messages.error(request, msg)
                return redirect("signup")

            user = User.objects.create_user(username=email, password=password)
            user.first_name = full_name
            user.email = email
            user.save()

            if _is_json(request):
                return JsonResponse({'status': 'success', 'message': 'Account created successfully!', 'name': full_name}, status=201)
            messages.success(request, "Account created successfully. Please sign in.")
            return redirect("login")
            
        except Exception as e:
            if _is_json(request):
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            messages.error(request, "Signup failed. Please try again.")
            return redirect("signup")

@csrf_exempt
def login_view(request):
    if request.method == "GET":
        return render(request, "auth/login.html")
    """
    Authenticates a user and starts a session.
    
    Args:
        request (HttpRequest): The HTTP request containing login credentials.
        
    Returns:
        JsonResponse: Success status with username or invalid credentials error.
    """
    if request.method == "POST":
        data = _body_or_post(request)
        username = (data.get("username") or data.get("email") or "").strip()
        password = data.get("password") or ""
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            if _is_json(request):
                return JsonResponse({"status": "success", "name": user.first_name or user.get_username()})
            return redirect("dashboard")
        if _is_json(request):
            return JsonResponse({"message": "Invalid credentials"}, status=400)
        messages.error(request, "Invalid email or password.")
        return redirect("login")
    
@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """
    Logs out the user and terminates the current session.
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponseRedirect: Redirect to login.
    """ 
    logout(request)
    return redirect("login")
