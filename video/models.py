from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Room(models.Model):
    """Represents a video conference room."""
    name = models.CharField(max_length=255, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Note(models.Model):
    """Represents presentation notes for a room."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.room.name} at {self.created_at}"

class Attendance(models.Model):
    """Tracks student attendance in a room."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance')
    join_time = models.DateTimeField(auto_now_add=True)
    leave_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} in {self.room.name}"

    class Meta:
        # Ensures a student can't have multiple open attendance records for the same room
        unique_together = ('room', 'student', 'leave_time')

class Profile(models.Model):
    """Extends the default User model to include roles."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_lecturer = models.BooleanField(default=False)

    def __str__(self):
        role = "Lecturer" if self.is_lecturer else "Student"
        return f"{self.user.username} - {role}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile for each new User."""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the Profile when the User is saved."""
    instance.profile.save()
