# video/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.index, name="index"),
    path("<str:room_name>/", views.room, name="room"),
    path("<str:room_name>/attendance/download/", views.download_attendance, name="download_attendance"),
    path("<str:room_name>/notes/", views.manage_notes, name="manage_notes"),
]
