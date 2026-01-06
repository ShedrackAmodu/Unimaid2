from django.contrib import admin
from django.utils import timezone
from .models import Loan, Reservation, Fine


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_copy', 'loan_date', 'due_date', 'status']
    list_filter = ['status', 'loan_date', 'due_date']
    search_fields = ['user__username', 'book_copy__book__title']
    actions = ['process_return']

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


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount', 'reason', 'status', 'paid_date']
    list_filter = ['status']
    search_fields = ['loan__user__username', 'reason']
