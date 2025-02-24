from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Create your views here.

site = "Hekima"

def login(request):
    if request.method == "POST":
        pass
    
    context = {
        "site": site,
    }
    template_name = "accounts/login.html"
    
    return render(request, template_name, context)

@login_required
def home(request):
    context = {
        "site": site,
    }
    template_name = "base.html"
    
    return render(request, template_name, context)