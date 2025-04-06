from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import status

site = "Hekima"

def login_view(request):  # Renamed to avoid conflict with Django's `login` function
    if request.method == "POST":
        print(f"\nThe request: {request.POST}\n")
        
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        print(f"\nAttempting login: {username}, {password}\n")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse(
                {"message": "Success", "redirect_url": "/"},
                status=status.HTTP_200_OK
            )
        else:
            return JsonResponse(
                {"error": "Invalid username or password. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

    context = {"site": site}
    return render(request, "accounts/login.html", context)

@login_required
def home(request):
    context = {"site": site}
    return render(request, "base.html", context)
