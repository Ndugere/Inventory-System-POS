from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# Create your views here.

site = "Hekima"

def login(request):
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