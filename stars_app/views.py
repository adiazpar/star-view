from django.shortcuts import render, redirect

# Importing other things from project files. Follow the principle of least privilege
# and only import what you NEED to use, not the whole file (like *)
from .models import User
from stars_app.models import Location, Event

# Authentication libraries:
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# To display error/success messages:
from django.contrib import messages

# rest framework
from rest_framework import viewsets
from stars_app.serializers import LocationSerializer, EventSerializer

# ---------------------------------------------------------------- #
# Navigation Views:
def home(request):
    return render(request, 'stars_app/home.html')

def map(request):
    return render(request, 'stars_app/map.html')


# ---------------------------------------------------------------- #
# Authentication Views:
def register(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            pass1 = request.POST.get('password1')
            pass2 = request.POST.get('password2')

            # We are going to define a user filter to check for existing usernames:
            user = User.objects.filter(username=username.lower())

            # Check if the username already exists in our database:
            if user.exists():
                messages.error(request, 'Username already exists...')
                return redirect('register')

            # Check if the password confirmation doesn't match:
            if pass1 != pass2:
                messages.error(request, 'Passwords do not match...')
                return redirect('register')

            # We are creating a user after verifying everything is correct:
            user = User.objects.create(username=username.lower(), email=email)
            user.set_password(pass1)
            user.save()

            # Notify the user that their account has been created successfully:
            messages.success(request, 'Account created successfully')
            return redirect('login')

        except Exception as e:
            # Display a message to the user that registration was unsuccessful:
            messages.error(request, 'Something went wrong...')
            return redirect('register')

    # If we didn't call a post method, direct user to register page:
    return render(request, 'stars_app/register.html')

def custom_login(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')

            # We are getting the user model from an imported library in models.py:
            user = User.objects.filter(username=username.lower())

            # Check for the case that the user doesn't exist in our database:
            if not user.exists():
                messages.error(request, 'Username not found')
                return redirect('login')

            # Check for matching username & password:
            user = authenticate(request, username=username.lower(), password=password)
            if user is not None:
                login(request, user)
                return redirect('home')     # Low-key I hate this shit can we redirect it to user's previous page?

            # If user couldn't authenticate above, display wrong password message:
            messages.error(request, 'Wrong password...')
            return redirect('login')

        except Exception as e:
            # Display a message to the user that login was unsuccessful:
            messages.error(request, 'Something went wrong...')
            return redirect('home')

    # If we didn't call a post method, direct user to login page:
    return render(request, 'stars_app/login.html')

@login_required(login_url='/login/')
def custom_logout(request):
    logout(request)
    return redirect('home')

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer