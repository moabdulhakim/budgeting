import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('username')  
            password = data.get('password')
            full_name = data.get('name')

            if User.objects.filter(username=email).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'This email is already registered.'
                }, status=400)

            user = User.objects.create_user(username=email, password=password)
            user.first_name = full_name
            user.save()

            return JsonResponse({
                'status': 'success', 
                'message': 'Account created successfully!',
                'name': full_name
            }, status=201)
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user = authenticate(username=data["username"], password=data["password"])
        if user:
            login(request, user)
            return JsonResponse({"status": "success", "name": user.username})
        return JsonResponse({"message": "Invalid credentials"}, status=400) 
    
@csrf_exempt
def logout_view(request):
    logout(request)
    return JsonResponse({"status": "success"})
