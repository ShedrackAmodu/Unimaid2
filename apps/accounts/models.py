from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
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
    qr_code = models.ImageField(upload_to='qr_codes/users/', blank=True, null=True, help_text="QR code image for the user")

    objects = UserManager()

    def generate_qr_code(self):
        """Generate QR code containing user information."""
        # Create data string with user details
        user_id = self.student_id or self.faculty_id or str(self.id)
        data = f"User: {self.first_name} {self.last_name}\nID: {user_id}\nUsername: {self.username}\nType: {self.get_membership_type_display()}"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Save to model field
        filename = f"user_{self.id}_qr.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Generate QR code if not exists
        if not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

    class Meta:
        verbose_name = "Library User"
        verbose_name_plural = "Library Users"


class StudyRoom(BaseModel):
    ROOM_TYPE_CHOICES = [
        ('individual', 'Individual Study Room'),
        ('group', 'Group Study Room'),
        ('presentation', 'Presentation Room'),
    ]

    name = models.CharField(max_length=100, help_text="Name of the study room")
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES,
        help_text="Type of study room"
    )
    capacity = models.PositiveIntegerField(help_text="Maximum number of people")
    features = models.JSONField(default=list, help_text="List of room features")
    is_active = models.BooleanField(default=True, help_text="Whether the room is available for booking")
    location = models.CharField(max_length=200, blank=True, help_text="Location description")

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

    class Meta:
        verbose_name = "Study Room"
        verbose_name_plural = "Study Rooms"


class StudyRoomBooking(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='study_room_bookings')
    room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField(help_text="Booking date")
    start_time = models.TimeField(help_text="Start time")
    end_time = models.TimeField(help_text="End time")
    duration_hours = models.PositiveIntegerField(help_text="Duration in hours")
    number_of_people = models.PositiveIntegerField(default=1, help_text="Number of people using the room")
    purpose = models.TextField(blank=True, help_text="Purpose of booking")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Booking status"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")

    def __str__(self):
        return f"{self.user.username} - {self.room.name} on {self.date}"

    class Meta:
        verbose_name = "Study Room Booking"
        verbose_name_plural = "Study Room Bookings"
        ordering = ['date', 'start_time']
        unique_together = ('room', 'date', 'start_time')  # Prevent double booking same time slot
