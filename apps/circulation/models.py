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
