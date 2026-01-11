from django.db import models
from django.utils import timezone
from datetime import timedelta
from config.models import BaseModel
from apps.accounts.models import LibraryUser
from apps.catalog.models import Book, BookCopy


class Loan(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    ]

    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='loans', help_text="User who borrowed the book")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='loans', help_text="The specific book copy loaned")
    loan_date = models.DateTimeField(default=timezone.now, help_text="Date and time the book was loaned")
    due_date = models.DateTimeField(help_text="Date the book is due to be returned")
    return_date = models.DateTimeField(null=True, blank=True, help_text="Date the book was actually returned")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="Current status of the loan")

    def calculate_due_date(self):
        """Calculate due date based on user membership type."""
        loan_periods = {
            'student': 14,  # 14 days
            'faculty': 30,  # 30 days
            'staff': 21,    # 21 days
            'public': 7,    # 7 days
        }
        days = loan_periods.get(self.user.membership_type, 7)  # default to 7 days
        return self.loan_date + timedelta(days=days)

    def __str__(self):
        return f"{self.user.username} - {self.book_copy.book.title}"

    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        ordering = ['-loan_date']


class Reservation(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='reservations', help_text="User who made the reservation")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations', help_text="The book being reserved")
    reservation_date = models.DateTimeField(default=timezone.now, help_text="Date the reservation was made")
    expiry_date = models.DateTimeField(help_text="Date the reservation expires")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="Current status of the reservation")

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ['-reservation_date']


class LoanRequest(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='loan_requests', help_text="User making the borrow request")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='loan_requests', help_text="The specific book copy requested")
    request_date = models.DateTimeField(default=timezone.now, help_text="Date the request was made")
    expiry_date = models.DateTimeField(help_text="Date the request expires if not processed")
    approval_date = models.DateTimeField(null=True, blank=True, help_text="Date the request was approved")
    rejection_date = models.DateTimeField(null=True, blank=True, help_text="Date the request was rejected")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of the request")
    notes = models.TextField(blank=True, help_text="Additional notes from staff or user")

    def save(self, *args, **kwargs):
        # Set expiry date to 24 hours from request if not set
        if not self.expiry_date:
            self.expiry_date = self.request_date + timedelta(hours=24)
        super().save(*args, **kwargs)

    def approve(self, approved_by):
        """Approve the loan request and create the actual loan."""
        if self.status != 'pending':
            raise ValueError("Only pending requests can be approved")

        # Create the loan
        loan = Loan.objects.create(
            user=self.user,
            book_copy=self.book_copy,
            due_date=timezone.now() + timedelta(days=14)  # Default, will be recalculated
        )
        loan.due_date = loan.calculate_due_date()
        loan.save()

        # Update book copy status
        self.book_copy.status = 'checked_out'
        self.book_copy.save()

        # Update request status
        self.status = 'approved'
        self.approval_date = timezone.now()
        self.save()

        return loan

    def reject(self, reason=""):
        """Reject the loan request."""
        if self.status != 'pending':
            raise ValueError("Only pending requests can be rejected")

        self.status = 'rejected'
        self.rejection_date = timezone.now()
        if reason:
            self.notes = reason
        self.save()

    def cancel(self):
        """Cancel the loan request."""
        if self.status != 'pending':
            raise ValueError("Only pending requests can be cancelled")

        self.status = 'cancelled'
        self.save()

    def __str__(self):
        return f"Borrow request: {self.user.username} - {self.book_copy.book.title}"

    class Meta:
        verbose_name = "Loan Request"
        verbose_name_plural = "Loan Requests"
        ordering = ['-request_date']


class Fine(BaseModel):
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('waived', 'Waived'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='fines', help_text="The loan this fine is associated with")
    amount = models.DecimalField(max_digits=8, decimal_places=2, help_text="Amount of the fine")
    reason = models.CharField(max_length=200, help_text="Reason for the fine")
    paid_date = models.DateTimeField(null=True, blank=True, help_text="Date the fine was paid")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid', help_text="Current status of the fine")

    def __str__(self):
        return f"Fine for {self.loan} - {self.amount}"

    class Meta:
        verbose_name = "Fine"
        verbose_name_plural = "Fines"
        ordering = ['-created_at']


class Attendance(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(LibraryUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances', help_text="Registered library user (null for visitors)")
    registration_number = models.CharField(max_length=50, blank=True, help_text="Student/Staff registration number")
    full_name = models.CharField(max_length=200, help_text="Full name of the visitor")
    department = models.CharField(max_length=100, blank=True, help_text="Department")
    faculty = models.CharField(max_length=100, blank=True, help_text="Faculty")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number")
    purpose = models.TextField(blank=True, help_text="What did you come to the library with")
    check_in = models.DateTimeField(default=timezone.now, help_text="Check-in date and time")
    check_out = models.DateTimeField(null=True, blank=True, help_text="Check-out date and time")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="Current attendance status")

    def check_out_visitor(self):
        """Mark the visitor as checked out."""
        if self.status == 'active':
            self.check_out = timezone.now()
            self.status = 'completed'
            self.save()

    def save(self, *args, **kwargs):
        # Auto-populate fields from user if linked
        if self.user:
            self.registration_number = self.registration_number or (self.user.student_id or self.user.faculty_id or '')
            self.full_name = self.full_name or self.user.get_full_name()
            self.department = self.department or self.user.department
            self.phone = self.phone or self.user.phone
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.check_in.date()}"

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        ordering = ['-check_in']
