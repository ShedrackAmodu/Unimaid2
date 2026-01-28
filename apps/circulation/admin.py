from django.contrib import admin
from django.utils import timezone
from .models import Loan, Reservation, Fine, LoanRequest, Attendance
from config.bulk_actions import (
    bulk_update_loan_status, bulk_extend_loans, bulk_calculate_fines,
    bulk_process_reservations, bulk_checkout_visitors
)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_copy', 'loan_date', 'due_date', 'status']
    list_filter = ['status', 'loan_date', 'due_date']
    search_fields = ['user__username', 'book_copy__book__title']
    actions = ['process_return', bulk_update_loan_status, bulk_extend_loans, bulk_calculate_fines]

    def process_return(self, request, queryset):
        updated = 0
        for loan in queryset:
            loan.status = 'returned'
            loan.return_date = timezone.now()
            loan.book_copy.status = 'available'
            loan.book_copy.save()
            loan.save()
            updated += 1
        self.message_user(request, f'{updated} loans processed as returned.')
    process_return.short_description = 'Process return for selected loans'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'reservation_date', 'status']
    list_filter = ['status', 'reservation_date']
    search_fields = ['user__username', 'book__title']
    actions = [bulk_process_reservations]


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount', 'reason', 'status', 'paid_date']
    list_filter = ['status']
    search_fields = ['loan__user__username', 'reason']


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_copy', 'request_date', 'status', 'expiry_date']
    list_filter = ['status', 'request_date', 'expiry_date']
    search_fields = ['user__username', 'book_copy__book__title']
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        approved = 0
        for loan_request in queryset.filter(status='pending'):
            try:
                loan_request.approve(request.user)
                approved += 1
            except ValueError as e:
                self.message_user(request, f'Could not approve request for {loan_request}: {e}', level='error')
        self.message_user(request, f'{approved} loan requests approved.')
    approve_requests.short_description = 'Approve selected loan requests'

    def reject_requests(self, request, queryset):
        rejected = 0
        for loan_request in queryset.filter(status='pending'):
            loan_request.reject("Rejected by administrator")
            rejected += 1
        self.message_user(request, f'{rejected} loan requests rejected.')
    reject_requests.short_description = 'Reject selected loan requests'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'check_in', 'check_out', 'status']
    list_filter = ['status', 'check_in', 'check_out']
    search_fields = ['user__username', 'full_name', 'registration_number']
    actions = ['check_out_visitors', bulk_checkout_visitors]

    def check_out_visitors(self, request, queryset):
        updated = 0
        for attendance in queryset.filter(status='active'):
            attendance.check_out_visitor()
            updated += 1
        self.message_user(request, f'{updated} visitors checked out successfully.')
    check_out_visitors.short_description = 'Check out selected visitors'
