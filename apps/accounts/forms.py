from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import LibraryUser


class LibraryUserCreationForm(UserCreationForm):
    # Additional fields from template
    academic_year = forms.CharField(max_length=20, required=False, help_text="Academic year for students")
    alternate_phone = forms.CharField(max_length=20, required=False, help_text="Alternate phone number")
    address = forms.CharField(widget=forms.Textarea, required=False, help_text="Address")
    emergency_phone = forms.CharField(max_length=20, required=False, help_text="Emergency contact phone")
    emergency_relation = forms.CharField(max_length=50, required=False, help_text="Relationship to emergency contact")
    terms = forms.BooleanField(required=True, help_text="Agreement to terms and conditions")
    newsletter = forms.BooleanField(required=False, help_text="Subscribe to newsletter")

    class Meta:
        model = LibraryUser
        fields = ('username', 'email', 'first_name', 'last_name', 'membership_type',
                 'department', 'student_id', 'faculty_id', 'staff_id', 'phone', 'emergency_contact')


class LibraryUserChangeForm(UserChangeForm):
    password = None  # Remove password field from change form

    class Meta:
        model = LibraryUser
        fields = ('email', 'first_name', 'last_name', 'membership_type',
                 'department', 'student_id', 'faculty_id', 'staff_id', 'phone', 'emergency_contact')
