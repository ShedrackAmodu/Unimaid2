from django.contrib import admin
from .models import Event, EventRegistration
from config.bulk_actions import bulk_update_event_status


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'time', 'location', 'organizer']
    list_filter = ['date', 'location']
    search_fields = ['title', 'organizer__username']
    actions = [bulk_update_event_status]


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'user']
    list_filter = ['event__date']
    search_fields = ['event__title', 'user__username']
