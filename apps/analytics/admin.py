from django.contrib import admin
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from .models import AnalyticsEvent, DailyStats, PopularItem, SystemHealth


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    """Admin interface for AnalyticsEvent model."""
    list_display = [
        'event_type_display', 'user_link', 'formatted_timestamp',
        'item_info', 'session_id_short', 'ip_address'
    ]
    list_filter = [
        'event_type', 'created_at', 'user__membership_type'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'session_id', 'ip_address', 'search_query',
        'page_url', 'referrer'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'created_at')
        }),
        ('User Information', {
            'fields': ('user', 'session_id', 'ip_address', 'user_agent')
        }),
        ('Content Information', {
            'fields': ('page_url', 'search_query', 'book', 'document', 'referrer')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )

    def event_type_display(self, obj):
        """Display event type with color coding."""
        colors = {
            'login': 'success',
            'logout': 'secondary',
            'page_view': 'info',
            'search': 'primary',
            'checkout': 'warning',
            'return': 'success',
            'download': 'info',
            'registration': 'success',
        }
        color = colors.get(obj.event_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_display.short_description = 'Event Type'

    def user_link(self, obj):
        """Display user with link to admin."""
        if obj.user:
            url = reverse('admin:accounts_libraryuser_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'

    def formatted_timestamp(self, obj):
        """Format timestamp nicely."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    formatted_timestamp.short_description = 'Timestamp'

    def item_info(self, obj):
        """Display information about the item involved."""
        if obj.book:
            url = reverse('admin:catalog_book_change', args=[obj.book.id])
            return format_html('<a href="{}">📖 {}</a>', url, obj.book.title[:50])
        elif obj.document:
            url = reverse('admin:repository_document_change', args=[obj.document.id])
            return format_html('<a href="{}">📄 {}</a>', url, obj.document.title[:50])
        elif obj.search_query:
            return f'🔍 {obj.search_query[:50]}'
        elif obj.page_url:
            return f'🌐 {obj.page_url[:50]}'
        return '-'
    item_info.short_description = 'Item/Content'

    def session_id_short(self, obj):
        """Display shortened session ID."""
        if obj.session_id:
            return obj.session_id[:8] + '...'
        return '-'
    session_id_short.short_description = 'Session'


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    """Admin interface for DailyStats model."""
    list_display = [
        'date', 'user_stats', 'book_stats', 'loan_stats',
        'activity_stats', 'formatted_created_at'
    ]
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']

    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('User Statistics', {
            'fields': ('total_users', 'active_users', 'new_users')
        }),
        ('Book Statistics', {
            'fields': ('total_books', 'available_books', 'checked_out_books')
        }),
        ('Circulation Statistics', {
            'fields': ('total_loans', 'active_loans', 'overdue_loans', 'returned_today')
        }),
        ('Repository Statistics', {
            'fields': ('total_documents', 'document_downloads')
        }),
        ('Activity Statistics', {
            'fields': ('page_views', 'searches', 'logins')
        }),
    )

    def user_stats(self, obj):
        """Display user statistics summary."""
        return format_html(
            'Total: {}<br>Active: {}<br>New: {}',
            obj.total_users, obj.active_users, obj.new_users
        )
    user_stats.short_description = 'Users'

    def book_stats(self, obj):
        """Display book statistics summary."""
        return format_html(
            'Total: {}<br>Available: {}<br>Checked Out: {}',
            obj.total_books, obj.available_books, obj.checked_out_books
        )
    book_stats.short_description = 'Books'

    def loan_stats(self, obj):
        """Display loan statistics summary."""
        return format_html(
            'Total: {}<br>Active: {}<br>Overdue: {}<br>Returned: {}',
            obj.total_loans, obj.active_loans, obj.overdue_loans, obj.returned_today
        )
    loan_stats.short_description = 'Loans'

    def activity_stats(self, obj):
        """Display activity statistics summary."""
        return format_html(
            'Page Views: {}<br>Searches: {}<br>Logins: {}',
            obj.page_views, obj.searches, obj.logins
        )
    activity_stats.short_description = 'Activity'

    def formatted_created_at(self, obj):
        """Format created timestamp."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else '-'
    formatted_created_at.short_description = 'Created'

    actions = ['recalculate_stats']

    def recalculate_stats(self, request, queryset):
        """Recalculate statistics for selected dates."""
        from django.apps import apps
        from django.db.models import Q

        updated = 0
        for stat in queryset:
            # Recalculate user stats
            LibraryUser = apps.get_model('accounts', 'LibraryUser')
            stat.total_users = LibraryUser.objects.count()
            stat.active_users = LibraryUser.objects.filter(
                last_login__date__gte=stat.date - timezone.timedelta(days=30)
            ).count()
            stat.new_users = LibraryUser.objects.filter(
                date_joined__date=stat.date
            ).count()

            # Recalculate book stats
            Book = apps.get_model('catalog', 'Book')
            BookCopy = apps.get_model('catalog', 'BookCopy')
            stat.total_books = Book.objects.active().count()
            stat.available_books = BookCopy.objects.filter(status='available').count()
            stat.checked_out_books = BookCopy.objects.filter(status='checked_out').count()

            # Recalculate loan stats
            Loan = apps.get_model('circulation', 'Loan')
            stat.total_loans = Loan.objects.count()
            stat.active_loans = Loan.objects.filter(status='active').count()
            stat.overdue_loans = Loan.objects.filter(
                status='active',
                due_date__date__lt=stat.date
            ).count()
            stat.returned_today = Loan.objects.filter(
                status='returned',
                return_date__date=stat.date
            ).count()

            # Recalculate activity stats
            stat.page_views = AnalyticsEvent.objects.filter(
                event_type='page_view',
                created_at__date=stat.date
            ).count()
            stat.searches = AnalyticsEvent.objects.filter(
                event_type='search',
                created_at__date=stat.date
            ).count()
            stat.logins = AnalyticsEvent.objects.filter(
                event_type='login',
                created_at__date=stat.date
            ).count()

            stat.save()
            updated += 1

        self.message_user(
            request,
            f'Successfully recalculated statistics for {updated} days.'
        )
    recalculate_stats.short_description = 'Recalculate selected statistics'


@admin.register(PopularItem)
class PopularItemAdmin(admin.ModelAdmin):
    """Admin interface for PopularItem model."""
    list_display = [
        'item_type_display', 'item_link', 'total_score',
        'view_count', 'checkout_count', 'search_count', 'last_updated'
    ]
    list_filter = ['item_type', 'last_updated']
    search_fields = [
        'book__title', 'document__title'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_score']
    ordering = ['-total_score']

    fieldsets = (
        ('Item Information', {
            'fields': ('item_type', 'book', 'document')
        }),
        ('Popularity Metrics', {
            'fields': ('view_count', 'checkout_count', 'search_count', 'total_score')
        }),
        ('Metadata', {
            'fields': ('last_updated', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def item_type_display(self, obj):
        """Display item type with icon."""
        icons = {
            'book': '📖',
            'document': '📄'
        }
        icon = icons.get(obj.item_type, '❓')
        return f'{icon} {obj.get_item_type_display()}'
    item_type_display.short_description = 'Type'

    def item_link(self, obj):
        """Display item with link to admin."""
        if obj.item_type == 'book' and obj.book:
            url = reverse('admin:catalog_book_change', args=[obj.book.id])
            return format_html('<a href="{}">{}</a>', url, obj.book.title[:50])
        elif obj.item_type == 'document' and obj.document:
            url = reverse('admin:repository_document_change', args=[obj.document.id])
            return format_html('<a href="{}">{}</a>', url, obj.document.title[:50])
        return 'Unknown Item'
    item_link.short_description = 'Item'

    actions = ['update_scores', 'reset_scores']

    def update_scores(self, request, queryset):
        """Update popularity scores for selected items."""
        updated = 0
        for item in queryset:
            item.update_score()
            updated += 1

        self.message_user(
            request,
            f'Successfully updated popularity scores for {updated} items.'
        )
    update_scores.short_description = 'Update popularity scores'

    def reset_scores(self, request, queryset):
        """Reset popularity scores to zero."""
        updated = queryset.update(
            view_count=0,
            checkout_count=0,
            search_count=0,
            total_score=0
        )
        self.message_user(
            request,
            f'Successfully reset popularity scores for {updated} items.'
        )
    reset_scores.short_description = 'Reset all scores to zero'


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    """Admin interface for SystemHealth model."""
    list_display = [
        'checked_at', 'response_time_display', 'cpu_usage_display',
        'memory_usage_display', 'error_count', 'status_indicator'
    ]
    list_filter = ['checked_at']
    search_fields = ['last_error']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'checked_at'
    ]
    date_hierarchy = 'checked_at'
    ordering = ['-checked_at']
    list_per_page = 50

    fieldsets = (
        ('Timestamp', {
            'fields': ('checked_at',)
        }),
        ('Performance Metrics', {
            'fields': ('response_time', 'cpu_usage', 'memory_usage', 'disk_usage')
        }),
        ('System Status', {
            'fields': ('db_connections', 'db_query_count')
        }),
        ('Errors', {
            'fields': ('error_count', 'last_error')
        }),
    )

    def response_time_display(self, obj):
        """Display response time with color coding."""
        if obj.response_time is None:
            return '-'

        if obj.response_time < 1.0:
            color = 'success'
        elif obj.response_time < 2.0:
            color = 'warning'
        else:
            color = 'danger'

        return format_html(
            '<span class="badge bg-{}">{:.2f}s</span>',
            color, obj.response_time
        )
    response_time_display.short_description = 'Response Time'

    def cpu_usage_display(self, obj):
        """Display CPU usage with color coding."""
        if obj.cpu_usage is None:
            return '-'

        if obj.cpu_usage < 50:
            color = 'success'
        elif obj.cpu_usage < 80:
            color = 'warning'
        else:
            color = 'danger'

        return format_html(
            '<span class="badge bg-{}">{:.1f}%</span>',
            color, obj.cpu_usage
        )
    cpu_usage_display.short_description = 'CPU Usage'

    def memory_usage_display(self, obj):
        """Display memory usage with color coding."""
        if obj.memory_usage is None:
            return '-'

        if obj.memory_usage < 70:
            color = 'success'
        elif obj.memory_usage < 90:
            color = 'warning'
        else:
            color = 'danger'

        return format_html(
            '<span class="badge bg-{}">{:.1f}%</span>',
            color, obj.memory_usage
        )
    memory_usage_display.short_description = 'Memory Usage'

    def status_indicator(self, obj):
        """Display overall system status."""
        if obj.error_count > 0:
            return format_html('<span class="badge bg-danger">⚠️ Issues</span>')
        elif obj.response_time and obj.response_time > 2.0:
            return format_html('<span class="badge bg-warning">🐌 Slow</span>')
        else:
            return format_html('<span class="badge bg-success">✅ Healthy</span>')
    status_indicator.short_description = 'Status'

    actions = ['clear_old_records']

    def clear_old_records(self, request, queryset):
        """Clear old system health records (keep last 1000)."""
        # This would be implemented to clean up old records
        # For now, just show a message
        self.message_user(
            request,
            'Old records cleanup not yet implemented. Use Django management commands for data cleanup.'
        )
    clear_old_records.short_description = 'Clear old records (keep recent 1000)'
