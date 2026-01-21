from rest_framework import serializers
from .models import AnalyticsEvent, DailyStats, PopularItem, SystemHealth


class AnalyticsEventSerializer(serializers.ModelSerializer):
    """Serializer for AnalyticsEvent model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = AnalyticsEvent
        fields = [
            'id', 'event_type', 'event_type_display', 'user', 'user_name',
            'session_id', 'ip_address', 'user_agent', 'page_url', 'search_query',
            'book', 'book_title', 'document', 'document_title', 'referrer',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DailyStatsSerializer(serializers.ModelSerializer):
    """Serializer for DailyStats model."""

    class Meta:
        model = DailyStats
        fields = [
            'id', 'date', 'total_users', 'active_users', 'new_users',
            'total_books', 'available_books', 'checked_out_books',
            'total_loans', 'active_loans', 'overdue_loans', 'returned_today',
            'total_documents', 'document_downloads', 'page_views', 'searches', 'logins'
        ]
        read_only_fields = ['id']


class PopularItemSerializer(serializers.ModelSerializer):
    """Serializer for PopularItem model."""
    book_title = serializers.CharField(source='book.title', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    item_title = serializers.SerializerMethodField()

    class Meta:
        model = PopularItem
        fields = [
            'id', 'item_type', 'book', 'book_title', 'document', 'document_title',
            'item_title', 'view_count', 'checkout_count', 'search_count',
            'total_score', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']

    def get_item_title(self, obj):
        if obj.item_type == 'book' and obj.book:
            return obj.book.title
        elif obj.item_type == 'document' and obj.document:
            return obj.document.title
        return ""


class SystemHealthSerializer(serializers.ModelSerializer):
    """Serializer for SystemHealth model."""

    class Meta:
        model = SystemHealth
        fields = [
            'id', 'response_time', 'cpu_usage', 'memory_usage', 'disk_usage',
            'error_count', 'last_error', 'db_connections', 'db_query_count',
            'checked_at'
        ]
        read_only_fields = ['id', 'checked_at']


class AnalyticsDashboardSerializer(serializers.Serializer):
    """Serializer for analytics dashboard data."""
    daily_stats = DailyStatsSerializer(many=True, read_only=True)
    popular_books = PopularItemSerializer(many=True, read_only=True)
    popular_documents = PopularItemSerializer(many=True, read_only=True)
    recent_events = AnalyticsEventSerializer(many=True, read_only=True)
    system_health = SystemHealthSerializer(read_only=True)

    # Summary statistics
    total_users = serializers.IntegerField(read_only=True)
    total_books = serializers.IntegerField(read_only=True)
    total_loans = serializers.IntegerField(read_only=True)
    total_documents = serializers.IntegerField(read_only=True)
    active_loans = serializers.IntegerField(read_only=True)
    overdue_loans = serializers.IntegerField(read_only=True)
