from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import AnalyticsEvent, DailyStats, PopularItem, SystemHealth
from .serializers import (
    AnalyticsEventSerializer, DailyStatsSerializer, PopularItemSerializer,
    SystemHealthSerializer, AnalyticsDashboardSerializer
)


class AnalyticsEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AnalyticsEvent model."""
    queryset = AnalyticsEvent.objects.all()
    serializer_class = AnalyticsEventSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = AnalyticsEvent.objects.all()
        event_type = self.request.query_params.get('event_type', None)
        user = self.request.query_params.get('user', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)

        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if user:
            queryset = queryset.filter(user_id=user)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset


class DailyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DailyStats model."""
    queryset = DailyStats.objects.all()
    serializer_class = DailyStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DailyStats.objects.all()
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30

        # Get stats for the last N days
        date_from = timezone.now().date() - timedelta(days=days)
        return queryset.filter(date__gte=date_from)


class PopularItemViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PopularItem model."""
    queryset = PopularItem.objects.all()
    serializer_class = PopularItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PopularItem.objects.all()
        item_type = self.request.query_params.get('item_type', None)
        limit = self.request.query_params.get('limit', 10)

        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        if item_type:
            queryset = queryset.filter(item_type=item_type)

        return queryset[:limit]


class SystemHealthViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SystemHealth model."""
    queryset = SystemHealth.objects.all()
    serializer_class = SystemHealthSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = SystemHealth.objects.all()
        hours = self.request.query_params.get('hours', 24)
        try:
            hours = int(hours)
        except ValueError:
            hours = 24

        # Get health checks for the last N hours
        time_from = timezone.now() - timedelta(hours=hours)
        return queryset.filter(checked_at__gte=time_from)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_event(request):
    """Track an analytics event."""
    event_type = request.data.get('event_type')
    metadata = request.data.get('metadata', {})

    if not event_type:
        return Response(
            {'error': 'event_type is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create the event
    event = AnalyticsEvent.objects.create(
        event_type=event_type,
        user=request.user,
        session_id=request.session.session_key,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        page_url=request.data.get('page_url'),
        search_query=request.data.get('search_query'),
        referrer=request.data.get('referrer'),
        metadata=metadata
    )

    # Associate with book or document if provided
    if 'book_id' in request.data:
        from apps.catalog.models import Book
        try:
            book = Book.objects.get(id=request.data['book_id'])
            event.book = book
            event.save()
        except Book.DoesNotExist:
            pass

    if 'document_id' in request.data:
        from apps.repository.models import Document
        try:
            document = Document.objects.get(id=request.data['document_id'])
            event.document = document
            event.save()
        except Document.DoesNotExist:
            pass

    serializer = AnalyticsEventSerializer(event)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Get analytics dashboard data."""
    # Get date range (default last 30 days)
    days = request.query_params.get('days', 30)
    try:
        days = int(days)
    except ValueError:
        days = 30

    date_from = timezone.now().date() - timedelta(days=days)

    # Get daily stats
    daily_stats = DailyStats.objects.filter(date__gte=date_from).order_by('date')

    # Get popular items
    popular_books = PopularItem.objects.filter(
        item_type='book'
    ).order_by('-total_score')[:10]

    popular_documents = PopularItem.objects.filter(
        item_type='document'
    ).order_by('-total_score')[:10]

    # Get recent events
    recent_events = AnalyticsEvent.objects.all().order_by('-created_at')[:50]

    # Get latest system health
    system_health = SystemHealth.objects.first()

    # Calculate summary statistics
    from apps.accounts.models import LibraryUser
    from apps.catalog.models import Book
    from apps.circulation.models import Loan
    from apps.repository.models import Document

    total_users = LibraryUser.objects.count()
    total_books = Book.objects.count()
    total_loans = Loan.objects.count()
    total_documents = Document.objects.count()
    active_loans = Loan.objects.filter(status='active').count()
    overdue_loans = Loan.objects.filter(
        status='active',
        due_date__date__lt=timezone.now().date()
    ).count()

    dashboard_data = {
        'daily_stats': DailyStatsSerializer(daily_stats, many=True).data,
        'popular_books': PopularItemSerializer(popular_books, many=True).data,
        'popular_documents': PopularItemSerializer(popular_documents, many=True).data,
        'recent_events': AnalyticsEventSerializer(recent_events, many=True).data,
        'system_health': SystemHealthSerializer(system_health).data if system_health else None,
        'total_users': total_users,
        'total_books': total_books,
        'total_loans': total_loans,
        'total_documents': total_documents,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
    }

    return Response(dashboard_data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_daily_stats(request):
    """Update daily statistics (admin only)."""
    today = timezone.now().date()

    # Calculate statistics
    from apps.accounts.models import LibraryUser
    from apps.catalog.models import Book, BookCopy
    from apps.circulation.models import Loan
    from apps.repository.models import Document

    total_users = LibraryUser.objects.count()
    active_users = LibraryUser.objects.filter(
        last_login__date__gte=today - timedelta(days=30)
    ).count()
    new_users = LibraryUser.objects.filter(
        date_joined__date=today
    ).count()

    total_books = Book.objects.count()
    available_books = BookCopy.objects.filter(status='available').count()
    checked_out_books = BookCopy.objects.filter(status='checked_out').count()

    total_loans = Loan.objects.count()
    active_loans = Loan.objects.filter(status='active').count()
    overdue_loans = Loan.objects.filter(
        status='active',
        due_date__date__lt=today
    ).count()
    returned_today = Loan.objects.filter(
        status='returned',
        return_date__date=today
    ).count()

    total_documents = Document.objects.count()
    document_downloads = AnalyticsEvent.objects.filter(
        event_type='download',
        created_at__date=today
    ).count()

    page_views = AnalyticsEvent.objects.filter(
        event_type='page_view',
        created_at__date=today
    ).count()
    searches = AnalyticsEvent.objects.filter(
        event_type='search',
        created_at__date=today
    ).count()
    logins = AnalyticsEvent.objects.filter(
        event_type='login',
        created_at__date=today
    ).count()

    # Update or create daily stats
    stats, created = DailyStats.objects.get_or_create(
        date=today,
        defaults={
            'total_users': total_users,
            'active_users': active_users,
            'new_users': new_users,
            'total_books': total_books,
            'available_books': available_books,
            'checked_out_books': checked_out_books,
            'total_loans': total_loans,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'returned_today': returned_today,
            'total_documents': total_documents,
            'document_downloads': document_downloads,
            'page_views': page_views,
            'searches': searches,
            'logins': logins,
        }
    )

    if not created:
        stats.total_users = total_users
        stats.active_users = active_users
        stats.new_users = new_users
        stats.total_books = total_books
        stats.available_books = available_books
        stats.checked_out_books = checked_out_books
        stats.total_loans = total_loans
        stats.active_loans = active_loans
        stats.overdue_loans = overdue_loans
        stats.returned_today = returned_today
        stats.total_documents = total_documents
        stats.document_downloads = document_downloads
        stats.page_views = page_views
        stats.searches = searches
        stats.logins = logins
        stats.save()

    serializer = DailyStatsSerializer(stats)
    return Response(serializer.data, status=status.HTTP_200_OK)
