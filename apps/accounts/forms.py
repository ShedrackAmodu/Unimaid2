from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import LibraryUser


class LibraryUserCreationForm(UserCreationForm):
    class Meta:
        model = LibraryUser
        fields = ('username', 'email', 'first_name', 'last_name', 'membership_type',
                 'department', 'student_id', 'faculty_id', 'phone', 'emergency_contact')


class LibraryUserChangeForm(UserChangeForm):
    password = None  # Remove password field from change form

    class Meta:
        model = LibraryUser
        fields = ('email', 'first_name', 'last_name', 'membership_type',
                 'department', 'student_id', 'faculty_id', 'phone', 'emergency_contact')
