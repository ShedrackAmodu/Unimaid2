from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Loan, Reservation, LoanRequest, Fine, Attendance
from .serializers import (
    LoanSerializer, ReservationSerializer, LoanRequestSerializer,
    FineSerializer, AttendanceSerializer, CheckoutSerializer, ReturnSerializer
)


class LoanViewSet(viewsets.ModelViewSet):
    """ViewSet for Loan model."""
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Loan.objects.all()
        user = self.request.user
        status_filter = self.request.query_params.get('status', None)
        overdue_only = self.request.query_params.get('overdue_only', None)

        # Regular users can only see their own loans
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if overdue_only:
            today = timezone.now().date()
            queryset = queryset.filter(
                status='active',
                due_date__date__lt=today
            )

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_loans(self, request):
        """Get current user's loans."""
        queryset = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def renew(self, request, pk=None):
        """Renew a loan."""
        loan = self.get_object()

        # Check if user owns this loan or is staff
        if loan.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only renew your own loans'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if loan is active
        if loan.status != 'active':
            return Response(
                {'error': 'Only active loans can be renewed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Simple renewal logic - extend by 7 days
        from datetime import timedelta
        loan.due_date = timezone.now() + timedelta(days=7)
        loan.save()

        serializer = self.get_serializer(loan)
        return Response(serializer.data)


class ReservationViewSet(viewsets.ModelViewSet):
    """ViewSet for Reservation model."""
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Reservation.objects.all()
        user = self.request.user

        # Regular users can only see their own reservations
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LoanRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for LoanRequest model."""
    queryset = LoanRequest.objects.all()
    serializer_class = LoanRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = LoanRequest.objects.all()
        user = self.request.user
        status_filter = self.request.query_params.get('status', None)

        # Regular users can only see their own requests
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve a loan request (staff only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        loan_request = self.get_object()
        try:
            loan = loan_request.approve(request.user)
            return Response({
                'message': 'Request approved',
                'loan': LoanSerializer(loan).data
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject a loan request (staff only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        loan_request = self.get_object()
        reason = request.data.get('reason', '')
        try:
            loan_request.reject(reason)
            serializer = self.get_serializer(loan_request)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class FineViewSet(viewsets.ModelViewSet):
    """ViewSet for Fine model."""
    queryset = Fine.objects.all()
    serializer_class = FineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Fine.objects.all()
        user = self.request.user
        status_filter = self.request.query_params.get('status', None)

        # Regular users can only see their own fines
        if not user.is_staff:
            queryset = queryset.filter(loan__user=user)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pay(self, request, pk=None):
        """Mark a fine as paid."""
        fine = self.get_object()

        # Check permissions
        if fine.loan.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only pay your own fines'},
                status=status.HTTP_403_FORBIDDEN
            )

        fine.status = 'paid'
        fine.paid_date = timezone.now()
        fine.save()

        serializer = self.get_serializer(fine)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for Attendance model."""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Attendance.objects.all()
        user = self.request.user

        # Regular users can only see their own attendance
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def check_out(self, request, pk=None):
        """Check out a visitor."""
        attendance = self.get_object()

        # Check permissions
        if attendance.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only check out your own attendance'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            attendance.check_out_visitor()
            serializer = self.get_serializer(attendance)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_book(request):
    """Checkout a book."""
    serializer = CheckoutSerializer(data=request.data)
    if serializer.is_valid():
        book_copy_id = serializer.validated_data['book_copy_id']
        user_id = serializer.validated_data['user_id']

        # Check permissions
        if request.user.id != user_id and not request.user.is_staff:
            return Response(
                {'error': 'You can only checkout books for yourself'},
                status=status.HTTP_403_FORBIDDEN
            )

        from .models import BookCopy, Loan
        try:
            book_copy = BookCopy.objects.get(id=book_copy_id)

            # Create loan
            loan = Loan.objects.create(
                user_id=user_id,
                book_copy=book_copy
            )
            loan.due_date = loan.calculate_due_date()
            loan.save()

            # Update book copy status
            book_copy.status = 'checked_out'
            book_copy.save()

            return Response({
                'message': 'Book checked out successfully',
                'loan': LoanSerializer(loan).data
            }, status=status.HTTP_201_CREATED)

        except BookCopy.DoesNotExist:
            return Response(
                {'error': 'Book copy not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_book(request):
    """Return a book."""
    serializer = ReturnSerializer(data=request.data)
    if serializer.is_valid():
        loan_id = serializer.validated_data['loan_id']

        from .models import Loan
        try:
            loan = Loan.objects.get(id=loan_id)

            # Check permissions
            if loan.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'You can only return your own books'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Update loan
            loan.return_date = timezone.now()
            loan.status = 'returned'
            loan.save()

            # Update book copy status
            loan.book_copy.status = 'available'
            loan.book_copy.save()

            return Response({
                'message': 'Book returned successfully',
                'loan': LoanSerializer(loan).data
            })

        except Loan.DoesNotExist:
            return Response(
                {'error': 'Loan not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
