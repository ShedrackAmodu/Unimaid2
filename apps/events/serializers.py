from rest_framework import serializers
from .models import Event, EventRegistration


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model."""
    organizer_name = serializers.CharField(source='organizer.get_full_name', read_only=True)
    registrations_count = serializers.SerializerMethodField()
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'date', 'time', 'location', 'organizer',
            'organizer_name', 'max_attendees', 'registration_deadline', 'registrations_count',
            'available_spots', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_registrations_count(self, obj):
        return obj.registrations.count()

    def get_available_spots(self, obj):
        if obj.max_attendees:
            return max(0, obj.max_attendees - obj.registrations.count())
        return None


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for EventRegistration model."""
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateField(source='event.date', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'event_title', 'event_date', 'user', 'user_name', 'user_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_event(self, value):
        # Check if event has available spots
        if value.max_attendees and value.registrations.count() >= value.max_attendees:
            raise serializers.ValidationError("Event is full.")
        return value

    def validate(self, data):
        event = data.get('event')
        user = data.get('user')

        if event and user:
            # Check for duplicate registration
            if EventRegistration.objects.filter(event=event, user=user).exists():
                raise serializers.ValidationError("User is already registered for this event.")

            # Check registration deadline
            from django.utils import timezone
            if event.registration_deadline and timezone.now() > event.registration_deadline:
                raise serializers.ValidationError("Registration deadline has passed.")

        return data
