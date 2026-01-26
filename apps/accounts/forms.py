from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from .models import LibraryUser
import os


class LibraryUserCreationForm(UserCreationForm):
    # Only essential fields for registration - username and email only

    class Meta:
        model = LibraryUser
        fields = ('username', 'email')


class LibraryUserChangeForm(UserChangeForm):
    password = None  # Remove password field from change form
    
    class Meta:
        model = LibraryUser
        fields = ('email', 'first_name', 'last_name', 'membership_type',
                 'department', 'student_id', 'faculty_id', 'staff_id', 'phone', 
                 'emergency_contact', 'profile_picture', 'office_hours', 'position', 
                 'specialization')
        widgets = {
            'membership_type': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty_id': forms.TextInput(attrs={'class': 'form-control'}),
            'staff_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Emergency contact information'
            }),
            'office_hours': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Monday-Wednesday 9:00 AM - 5:00 PM'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Lecturer, Librarian'
            }),
            'specialization': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Area of expertise or specialization'
            }),
            'profile_picture': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            }),
        }

    def clean_profile_picture(self):
        """Validate profile picture upload."""
        profile_picture = self.cleaned_data.get('profile_picture')
        
        if profile_picture:
            # Check file size (max 2MB)
            if profile_picture.size > 2 * 1024 * 1024:
                raise ValidationError('Profile picture must be under 2MB.')
            
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            extension = os.path.splitext(profile_picture.name)[1].lower()
            if extension not in valid_extensions:
                raise ValidationError('Profile picture must be a JPG, PNG, or GIF file.')
            
            # Check image dimensions
            try:
                w, h = get_image_dimensions(profile_picture)
                if w < 100 or h < 100:
                    raise ValidationError('Profile picture must be at least 100x100 pixels.')
                if w > 2000 or h > 2000:
                    raise ValidationError('Profile picture must not exceed 2000x2000 pixels.')
            except Exception:
                raise ValidationError('Invalid image file.')
        
        return profile_picture

    def clean_student_id(self):
        """Validate student ID uniqueness."""
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            # Check if student_id is already taken by another user
            existing = LibraryUser.objects.filter(student_id=student_id).exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError('This student ID is already in use.')
        return student_id

    def clean_faculty_id(self):
        """Validate faculty ID uniqueness."""
        faculty_id = self.cleaned_data.get('faculty_id')
        if faculty_id:
            # Check if faculty_id is already taken by another user
            existing = LibraryUser.objects.filter(faculty_id=faculty_id).exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError('This faculty ID is already in use.')
        return faculty_id

    def clean_staff_id(self):
        """Validate staff ID uniqueness."""
        staff_id = self.cleaned_data.get('staff_id')
        if staff_id:
            # Check if staff_id is already taken by another user
            existing = LibraryUser.objects.filter(staff_id=staff_id).exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError('This staff ID is already in use.')
        return staff_id

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone number validation (Nigerian format)
            import re
            phone_pattern = re.compile(r'^(\+?234|0)?[789]\d{9}$')
            if not phone_pattern.match(phone.replace(' ', '')):
                raise ValidationError('Please enter a valid phone number.')
        return phone
