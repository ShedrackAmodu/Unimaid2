from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import LibraryUser


class LibraryUserCreationForm(UserCreationForm):
    # Only essential fields for registration
    membership_type = forms.ChoiceField(
        choices=LibraryUser.MEMBERSHIP_CHOICES,
        widget=forms.HiddenInput(),
        required=True
    )
    terms = forms.BooleanField(required=True, help_text="Agreement to terms and conditions")

    class Meta:
        model = LibraryUser
        fields = ('username', 'email', 'first_name', 'last_name')


class LibraryUserChangeForm(UserChangeForm):
    password = None  # Remove password field from change form

    class Meta:
        model = LibraryUser
        fields = ('email', 'first_name', 'last_name', 'membership_type',
                 'department', 'student_id', 'faculty_id', 'staff_id', 'phone', 'emergency_contact', 'profile_picture')
