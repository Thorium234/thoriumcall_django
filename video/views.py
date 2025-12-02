from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from .forms import CustomUserCreationForm, NoteForm
from .models import Room, Attendance, Note

# PDF Generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

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
    room, created = Room.objects.get_or_create(
        name=room_name,
        defaults={'host': request.user if request.user.profile.is_lecturer else None}
    )

    if not room.host and request.user.profile.is_lecturer:
        room.host = request.user
        room.save()

    notes = Note.objects.filter(room=room).order_by('-created_at')

    return render(request, "video/room.html", {
        "room_name": room.name,
        "is_host": room.host == request.user,
        "notes": notes,
    })

@login_required
def download_attendance(request, room_name):
    """Generate and serve a PDF of the attendance for a room."""
    room = get_object_or_404(Room, name=room_name)

    # Check if the user is the host
    if room.host != request.user:
        return HttpResponse("You are not authorized to view this page.", status=403)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_{room_name}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(inch, height - inch, f"Attendance Report for Room: {room.name}")

    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 1.5 * inch, f"Host: {room.host.username}")
    p.drawString(inch, height - 1.7 * inch, f"Date: {timezone.now().strftime('%Y-%m-%d')}")

    p.line(inch, height - 2 * inch, width - inch, height - 2 * inch)

    # Table Header
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.5 * inch, "Student")
    p.drawString(inch * 3, height - 2.5 * inch, "Join Time")
    p.drawString(inch * 5, height - 2.5 * inch, "Leave Time")
    p.drawString(inch * 7, height - 2.5 * inch, "Duration (mins)")

    p.setFont("Helvetica", 10)
    y = height - 2.8 * inch
    records = Attendance.objects.filter(room=room).order_by('student__username', 'join_time')
    
    for record in records:
        if y < inch: # New page if content gets too long
            p.showPage()
            y = height - inch
            p.setFont("Helvetica", 10)

        p.drawString(inch, y, record.student.username)
        p.drawString(inch * 3, y, record.join_time.strftime("%H:%M:%S"))
        
        duration_str = "In session"
        if record.leave_time:
            p.drawString(inch * 5, y, record.leave_time.strftime("%H:%M:%S"))
            duration = (record.leave_time - record.join_time).total_seconds() / 60
            duration_str = f"{duration:.2f}"
        else:
            p.drawString(inch * 5, y, "N/A")

        p.drawString(inch * 7, y, duration_str)
        y -= 0.3 * inch

    p.showPage()
    p.save()

    return response

@login_required
def manage_notes(request, room_name):
    """Allow host to add and see notes for a room."""
    room = get_object_or_404(Room, name=room_name)
    if request.user != room.host:
        return HttpResponse("You are not authorized to manage notes for this room.", status=403)

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.room = room
            note.save()
            return redirect('manage_notes', room_name=room.name)
    else:
        form = NoteForm()

    notes = Note.objects.filter(room=room).order_by('-created_at')
    return render(request, 'video/manage_notes.html', {
        'room': room,
        'notes': notes,
        'form': form
    })
