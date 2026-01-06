from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from config.models import BaseModel


class LibraryUser(AbstractUser, BaseModel):
    MEMBERSHIP_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('public', 'Public'),
    ]

    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_CHOICES,
        default='public',
        help_text="Type of library membership"
    )
    department = models.CharField(max_length=100, blank=True, help_text="Department or faculty for students/staff")
    student_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Student ID number")
    faculty_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Faculty/Staff ID number")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number")
    emergency_contact = models.TextField(blank=True, help_text="Emergency contact information")

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

    class Meta:
        verbose_name = "Library User"
        verbose_name_plural = "Library Users"
