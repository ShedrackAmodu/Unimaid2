from rest_framework import serializers
from .models import Loan, Reservation, LoanRequest, Fine, Attendance


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for Loan model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book_copy.book.title', read_only=True)
    book_isbn = serializers.CharField(source='book_copy.book.isbn', read_only=True)
    book_copy_barcode = serializers.CharField(source='book_copy.barcode', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            'id', 'user', 'user_name', 'user_username', 'book_copy', 'book_title',
            'book_isbn', 'book_copy_barcode', 'loan_date', 'due_date', 'return_date',
            'status', 'status_display', 'days_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_days_overdue(self, obj):
        if obj.status == 'active' and obj.due_date:
            from django.utils import timezone
            today = timezone.now().date()
            if today > obj.due_date.date():
                return (today - obj.due_date.date()).days
        return 0

    def create(self, validated_data):
        loan = super().create(validated_data)
        # Calculate due date if not provided
        if not loan.due_date:
            loan.due_date = loan.calculate_due_date()
            loan.save()
        return loan


class ReservationSerializer(serializers.ModelSerializer):
    """Serializer for Reservation model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_isbn = serializers.CharField(source='book.isbn', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'user_name', 'user_username', 'book', 'book_title', 'book_isbn',
            'reservation_date', 'expiry_date', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoanRequestSerializer(serializers.ModelSerializer):
    """Serializer for LoanRequest model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book_copy.book.title', read_only=True)
    book_copy_barcode = serializers.CharField(source='book_copy.barcode', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LoanRequest
        fields = [
            'id', 'user', 'user_name', 'user_username', 'book_copy', 'book_title',
            'book_copy_barcode', 'request_date', 'expiry_date', 'approval_date',
            'rejection_date', 'status', 'status_display', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'approval_date', 'rejection_date', 'created_at', 'updated_at']


class FineSerializer(serializers.ModelSerializer):
    """Serializer for Fine model."""
    loan_book_title = serializers.CharField(source='loan.book_copy.book.title', read_only=True)
    loan_user_name = serializers.CharField(source='loan.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Fine
        fields = [
            'id', 'loan', 'loan_book_title', 'loan_user_name', 'amount', 'reason',
            'paid_date', 'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'user_name', 'registration_number', 'full_name', 'department',
            'faculty', 'phone', 'purpose', 'check_in', 'check_out', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CheckoutSerializer(serializers.Serializer):
    """Serializer for book checkout."""
    book_copy_id = serializers.IntegerField(required=True)
    user_id = serializers.IntegerField(required=True)

    def validate_book_copy_id(self, value):
        from .models import BookCopy
        try:
            book_copy = BookCopy.objects.get(id=value)
            if book_copy.status != 'available':
                raise serializers.ValidationError("Book copy is not available for checkout.")
            return value
        except BookCopy.DoesNotExist:
            raise serializers.ValidationError("Book copy not found.")

    def validate_user_id(self, value):
        from apps.accounts.models import LibraryUser
        try:
            user = LibraryUser.objects.get(id=value)
            if not user.is_active:
                raise serializers.ValidationError("User account is not active.")
            return value
        except LibraryUser.DoesNotExist:
            raise serializers.ValidationError("User not found.")


class ReturnSerializer(serializers.Serializer):
    """Serializer for book return."""
    loan_id = serializers.IntegerField(required=True)

    def validate_loan_id(self, value):
        from .models import Loan
        try:
            loan = Loan.objects.get(id=value, status='active')
            return value
        except Loan.DoesNotExist:
            raise serializers.ValidationError("Active loan not found.")
