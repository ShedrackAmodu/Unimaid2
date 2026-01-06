from django.db import models
from config.models import BaseModel
from apps.accounts.models import LibraryUser


class EventRegistration(BaseModel):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='event_registrations')

    class Meta:
        unique_together = ('event', 'user')
        verbose_name = "Event Registration"
        verbose_name_plural = "Event Registrations"

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


class Event(BaseModel):
    title = models.CharField(max_length=500, help_text="Title of the event")
    description = models.TextField(help_text="Description of the event")
    date = models.DateField(help_text="Date of the event")
    time = models.TimeField(help_text="Time of the event")
    location = models.CharField(max_length=200, help_text="Location of the event")
    organizer = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='organized_events',
        help_text="User organizing the event"
    )
    max_attendees = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of attendees")
    registration_deadline = models.DateTimeField(null=True, blank=True, help_text="Deadline for registration")

    def __str__(self):
        return f"{self.title} - {self.date}"

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['date', 'time']
