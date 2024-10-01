from django.shortcuts import render, redirect

# Create your views here.
def home(request):
    return render(request, 'stars_app/home.html')

def map(request):
    return render(request, 'stars_app/map.html')
