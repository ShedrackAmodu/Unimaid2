from django.contrib import admin
from .models import LibraryUser


@admin.register(LibraryUser)
class LibraryUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'membership_type', 'email']
    list_filter = ['membership_type', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
