from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import LibraryUser
from config.admin_mixins import BaseAdminMixin, ExportMixin


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
