from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import LibraryUser, StudyRoom, StudyRoomBooking
from .serializers import (
    LibraryUserSerializer, LoginSerializer, StudyRoomSerializer,
    StudyRoomBookingSerializer
)


class LibraryUserViewSet(viewsets.ModelViewSet):
    """ViewSet for LibraryUser model."""
    queryset = LibraryUser.objects.all()
    serializer_class = LibraryUserSerializer

    def get_queryset(self):
        queryset = LibraryUser.objects.all()
        membership_type = self.request.query_params.get('membership_type', None)
        is_active = self.request.query_params.get('is_active', None)
        department = self.request.query_params.get('department', None)

        if membership_type:
            queryset = queryset.filter(membership_type=membership_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if department:
            queryset = queryset.filter(department=department)

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current user profile."""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudyRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for StudyRoom model."""
    queryset = StudyRoom.objects.filter(is_active=True)
    serializer_class = StudyRoomSerializer
    permission_classes = [IsAuthenticated]


class StudyRoomBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for StudyRoomBooking model."""
    queryset = StudyRoomBooking.objects.all()
    serializer_class = StudyRoomBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = StudyRoomBooking.objects.all()
        user = self.request.user
        room_id = self.request.query_params.get('room', None)
        date = self.request.query_params.get('date', None)
        status_filter = self.request.query_params.get('status', None)

        # Regular users can only see their own bookings
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        if room_id:
            queryset = queryset.filter(room_id=room_id)
        if date:
            queryset = queryset.filter(date=date)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def available_slots(self, request):
        """Get available booking slots for a room and date."""
        room_id = request.query_params.get('room')
        date = request.query_params.get('date')

        if not room_id or not date:
            return Response(
                {'error': 'room and date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            room = StudyRoom.objects.get(id=room_id, is_active=True)
            # Get existing bookings for the date
            existing_bookings = StudyRoomBooking.objects.filter(
                room=room,
                date=date,
                status__in=['pending', 'confirmed']
            ).values_list('start_time', 'end_time')

            # Simple availability check - in a real implementation,
            # you'd want more sophisticated time slot management
            available_slots = []
            # This is a simplified example - you'd implement proper time slot logic

            return Response({
                'room': StudyRoomSerializer(room).data,
                'date': date,
                'existing_bookings': list(existing_bookings),
                'available_slots': available_slots
            })

        except StudyRoom.DoesNotExist:
            return Response(
                {'error': 'Room not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'token': token.key,
            'user': LibraryUserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """User logout endpoint."""
    request.user.auth_token.delete()
    return Response({'message': 'Successfully logged out'})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint."""
    serializer = LibraryUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': LibraryUserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
