from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import Room

def register(request):
    """Handle user registration."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'video/register.html', {'form': form})

def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'video/login.html', {'form': form})

def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('index')

@login_required
def index(request):
    """Lobby page where users can enter a room name."""
    return render(request, "video/index.html")

@login_required
def room(request, room_name):
    """Video conference room page."""
    # Find the room or create a new one
    room, created = Room.objects.get_or_create(name=room_name)

    # If a new room is created and the user is a lecturer, make them the host.
    if created and request.user.profile.is_lecturer:
        room.host = request.user
        room.save()

    return render(request, "video/room.html", {
        "room_name": room.name,
        "is_host": room.host == request.user
    })
