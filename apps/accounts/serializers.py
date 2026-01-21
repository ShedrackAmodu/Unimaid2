from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import LibraryUser, StudyRoom, StudyRoomBooking


class LibraryUserSerializer(serializers.ModelSerializer):
    """Serializer for LibraryUser model."""
    full_name = serializers.SerializerMethodField()
    membership_type_display = serializers.CharField(source='get_membership_type_display', read_only=True)

    class Meta:
        model = LibraryUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'membership_type', 'membership_type_display', 'is_staff_approved',
            'email_verified', 'department', 'student_id', 'faculty_id', 'staff_id',
            'phone', 'emergency_contact', 'profile_picture', 'qr_code',
            'date_joined', 'last_login', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active', 'qr_code']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_full_name(self, obj):
        return obj.get_full_name()

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include username and password.')

        return data


class StudyRoomSerializer(serializers.ModelSerializer):
    """Serializer for StudyRoom model."""

    class Meta:
        model = StudyRoom
        fields = [
            'id', 'name', 'room_type', 'capacity', 'features',
            'is_active', 'location', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudyRoomBookingSerializer(serializers.ModelSerializer):
    """Serializer for StudyRoomBooking model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)

    class Meta:
        model = StudyRoomBooking
        fields = [
            'id', 'user', 'user_name', 'room', 'room_name', 'date', 'start_time',
            'end_time', 'duration_hours', 'number_of_people', 'purpose', 'status',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Check for booking conflicts
        room = data.get('room')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if room and date and start_time:
            conflicting_bookings = StudyRoomBooking.objects.filter(
                room=room,
                date=date,
                status__in=['pending', 'confirmed'],
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if self.instance:
                conflicting_bookings = conflicting_bookings.exclude(id=self.instance.id)

            if conflicting_bookings.exists():
                raise serializers.ValidationError('This time slot is already booked.')

        return data
