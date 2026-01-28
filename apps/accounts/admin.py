from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import LibraryUser, StudyRoom, StudyRoomBooking
from config.admin_mixins import BaseAdminMixin, ExportMixin
from config.bulk_actions import (
    bulk_activate_users, bulk_deactivate_users,
    bulk_update_membership_type, bulk_assign_department,
    bulk_update_study_room_status, bulk_update_booking_status
)


@admin.register(LibraryUser)
class LibraryUserAdmin(BaseAdminMixin, ExportMixin, UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'membership_type', 'is_active', 'date_joined', '_actions']
    list_filter = ['membership_type', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name',
                     'student_id', 'faculty_id']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email',
                                     'phone', 'emergency_contact')}),
        ('University Info', {'fields': ('membership_type', 'department',
                                       'student_id', 'faculty_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                   'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',
                      'first_name', 'last_name', 'membership_type'),
        }),
    )

    readonly_fields = ['last_login', 'date_joined']

    def get_queryset(self, request):
        """Custom queryset with annotations."""
        qs = super().get_queryset(request)
        return qs.select_related()

    def active_loans(self, obj):
        """Display count of active loans."""
        return obj.loans.filter(status='active').count()
    active_loans.short_description = 'Active Loans'

    def get_list_display(self, request):
        """Customize list display based on user permissions."""
        base_list = super().get_list_display(request)
        if request.user.is_superuser:
            return list(base_list) + ['active_loans']
        return base_list

    actions = ['activate_users', 'deactivate_users', 'export_as_csv']

    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated successfully.')
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(StudyRoom)
class StudyRoomAdmin(BaseAdminMixin, ExportMixin, admin.ModelAdmin):
    list_display = ['name', 'room_type', 'capacity', 'is_active', 'location', '_actions']
    list_filter = ['room_type', 'is_active', 'capacity']
    search_fields = ['name', 'location']
    ordering = ['name']

    fieldsets = (
        (None, {'fields': ('name', 'room_type', 'capacity', 'is_active')}),
        ('Details', {'fields': ('features', 'location')}),
    )

    actions = ['activate_rooms', 'deactivate_rooms', 'export_as_csv', bulk_update_study_room_status]

    def activate_rooms(self, request, queryset):
        """Activate selected rooms."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} rooms activated successfully.')
    activate_rooms.short_description = "Activate selected rooms"

    def deactivate_rooms(self, request, queryset):
        """Deactivate selected rooms."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} rooms deactivated successfully.')
    deactivate_rooms.short_description = "Deactivate selected rooms"


@admin.register(StudyRoomBooking)
class StudyRoomBookingAdmin(BaseAdminMixin, ExportMixin, admin.ModelAdmin):
    list_display = ['user', 'room', 'date', 'start_time', 'end_time', 'status', '_actions']
    list_filter = ['status', 'date', 'room__room_type']
    search_fields = ['user__username', 'user__email', 'room__name']
    ordering = ['-date', '-start_time']

    fieldsets = (
        (None, {'fields': ('user', 'room', 'date', 'start_time', 'end_time')}),
        ('Details', {'fields': ('duration_hours', 'number_of_people', 'purpose', 'status', 'notes')}),
    )

    readonly_fields = ['duration_hours']

    actions = ['confirm_bookings', 'cancel_bookings', 'export_as_csv', bulk_update_booking_status]

    def confirm_bookings(self, request, queryset):
        """Confirm selected bookings."""
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{updated} bookings confirmed successfully.')
    confirm_bookings.short_description = "Confirm selected bookings"

    def cancel_bookings(self, request, queryset):
        """Cancel selected bookings."""
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(status='cancelled')
        self.message_user(request, f'{updated} bookings cancelled successfully.')
    cancel_bookings.short_description = "Cancel selected bookings"
