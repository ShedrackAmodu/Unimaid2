from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.files.base import ContentFile
from django.utils import timezone
import qrcode
from io import BytesIO
from config.models import BaseModel


class EmailConfirmationToken(BaseModel):
    user = models.OneToOneField(
        'LibraryUser',
        on_delete=models.CASCADE,
        related_name='email_confirmation_token'
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Confirmation token for {self.user.username}"


class LibraryUser(AbstractUser, BaseModel):
    MEMBERSHIP_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('public', 'Public'),
    ]

    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_CHOICES,
        default='public',
        help_text="Type of library membership"
    )
    is_staff_approved = models.BooleanField(
        default=True,
        help_text="Whether staff membership has been approved by admin"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    department = models.CharField(max_length=100, blank=True, help_text="Department or faculty for students/staff")
    student_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Student ID number")
    faculty_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Faculty ID number")
    staff_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Staff ID number")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number")
    emergency_contact = models.TextField(blank=True, help_text="Emergency contact information")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, help_text="User profile picture")
    qr_code = models.ImageField(upload_to='qr_codes/users/', blank=True, null=True, help_text="QR code image for the user")

    objects = UserManager()

    def generate_qr_code(self):
        """Generate QR code containing user information."""
        # Create data string with user details
        user_id = self.student_id or self.faculty_id or self.staff_id or str(self.id)
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
        is_new = self.pk is None
        old_membership = None
        if not is_new:
            old_user = LibraryUser.objects.get(pk=self.pk)
            old_membership = old_user.membership_type

        # Set is_staff_approved for new staff users
        if is_new and self.membership_type == 'staff':
            self.is_staff_approved = False

        # Set is_active based on approval status and email verification for staff
        if self.membership_type == 'staff':
            self.is_active = self.is_staff_approved and self.email_verified
        elif not self.is_superuser:
            self.is_active = True

        super().save(*args, **kwargs)

        # Assign group based on membership_type if changed
        if is_new or old_membership != self.membership_type:
            self.assign_group_based_on_membership(is_new)
            # Save again to persist group and is_staff changes
            super().save(update_fields=['is_staff'])

        # Generate QR code if not exists
        if not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])

    def assign_group_based_on_membership(self, is_new=False):
        """Assign user to appropriate group based on membership_type."""
        from django.contrib.auth.models import Group

        # Clear existing groups (except for superusers who stay in Admin)
        if not self.is_superuser:
            self.groups.clear()

        # Map membership_type to group
        group_mapping = {
            'student': 'Patron',
            'faculty': 'Patron',
            'staff': 'Staff',
            'public': 'Patron',
        }

        group_name = group_mapping.get(self.membership_type)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                self.groups.add(group)
            except Group.DoesNotExist:
                pass  # Group not created yet

        # Superusers get Admin group
        if self.is_superuser:
            try:
                admin_group = Group.objects.get(name='Admin')
                self.groups.add(admin_group)
            except Group.DoesNotExist:
                pass

        # Set is_staff for Staff membership (don't save here to avoid recursion)
        if self.membership_type == 'staff':
            self.is_staff = True
            # Set approval status for staff
            if is_new:
                self.is_staff_approved = False
        elif not self.is_superuser:
            self.is_staff = False

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
