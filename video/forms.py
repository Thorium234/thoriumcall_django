# video/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    is_lecturer = forms.BooleanField(
        required=False,
        label="I am a lecturer",
        help_text="Select this if you will be hosting sessions."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Set the user's role based on the form input
            user.profile.is_lecturer = self.cleaned_data.get('is_lecturer', False)
            user.profile.save()
        return user
