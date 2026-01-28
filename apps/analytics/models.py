from django.db import models
from django.utils import timezone
from config.models import BaseModel


class AnalyticsEvent(BaseModel):
    """Model to track various analytics events."""

    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('book_view', 'Book View'),
        ('search', 'Search'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('checkout', 'Book Checkout'),
        ('return', 'Book Return'),
        ('reservation', 'Reservation'),
        ('download', 'Document Download'),
        ('registration', 'User Registration'),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, help_text="Type of analytics event")
    user = models.ForeignKey(
        'accounts.LibraryUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events',
        help_text="User who performed the event (null for anonymous)"
    )
    session_id = models.CharField(max_length=100, blank=True, help_text="Session identifier for anonymous users")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the user")
    user_agent = models.TextField(blank=True, help_text="User agent string")

    # Event-specific data
    page_url = models.URLField(blank=True, help_text="Page URL for page views")
    search_query = models.CharField(max_length=500, blank=True, help_text="Search query terms")
    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events',
        help_text="Book related to the event"
    )
    document = models.ForeignKey(
        'repository.EBook',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events',
        help_text="EBook related to the event"
    )

    # Metadata
    referrer = models.URLField(blank=True, help_text="Referrer URL")
    metadata = models.JSONField(default=dict, help_text="Additional event metadata")

    class Meta:
        verbose_name = "Analytics Event"
        verbose_name_plural = "Analytics Events"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]


class DailyStats(BaseModel):
    """Aggregated daily statistics."""

    date = models.DateField(unique=True, help_text="Date for these statistics")

    # User statistics
    total_users = models.PositiveIntegerField(default=0, help_text="Total registered users")
    active_users = models.PositiveIntegerField(default=0, help_text="Users active in the last 30 days")
    new_users = models.PositiveIntegerField(default=0, help_text="New user registrations")

    # Book statistics
    total_books = models.PositiveIntegerField(default=0, help_text="Total books in catalog")
    available_books = models.PositiveIntegerField(default=0, help_text="Available books")
    checked_out_books = models.PositiveIntegerField(default=0, help_text="Currently checked out books")

    # Circulation statistics
    total_loans = models.PositiveIntegerField(default=0, help_text="Total loans")
    active_loans = models.PositiveIntegerField(default=0, help_text="Currently active loans")
    overdue_loans = models.PositiveIntegerField(default=0, help_text="Overdue loans")
    returned_today = models.PositiveIntegerField(default=0, help_text="Books returned today")

    # Repository statistics
    total_documents = models.PositiveIntegerField(default=0, help_text="Total documents in repository")
    document_downloads = models.PositiveIntegerField(default=0, help_text="Document downloads today")

    # Activity statistics
    page_views = models.PositiveIntegerField(default=0, help_text="Total page views")
    searches = models.PositiveIntegerField(default=0, help_text="Total searches")
    logins = models.PositiveIntegerField(default=0, help_text="User logins")

    class Meta:
        verbose_name = "Daily Statistics"
        verbose_name_plural = "Daily Statistics"
        ordering = ['-date']


class PopularItem(BaseModel):
    """Track popularity of books and documents."""

    ITEM_TYPES = [
        ('book', 'Book'),
        ('document', 'Document'),
    ]

    item_type = models.CharField(max_length=10, choices=ITEM_TYPES, help_text="Type of item")
    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='popularity',
        help_text="Book (if item_type is book)"
    )
    document = models.ForeignKey(
        'repository.EBook',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='popularity',
        help_text="EBook (if item_type is document)"
    )

    # Popularity metrics
    view_count = models.PositiveIntegerField(default=0, help_text="Number of views")
    checkout_count = models.PositiveIntegerField(default=0, help_text="Number of checkouts/downloads")
    search_count = models.PositiveIntegerField(default=0, help_text="Number of searches")
    total_score = models.PositiveIntegerField(default=0, help_text="Combined popularity score")

    # Time periods
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Popular Item"
        verbose_name_plural = "Popular Items"
        unique_together = [
            ('item_type', 'book'),
            ('item_type', 'document'),
        ]
        ordering = ['-total_score']

    def update_score(self):
        """Update the popularity score based on various metrics."""
        # Simple scoring algorithm: views * 1 + checkouts * 5 + searches * 2
        self.total_score = (self.view_count * 1) + (self.checkout_count * 5) + (self.search_count * 2)
        self.save(update_fields=['total_score', 'last_updated'])


class SystemHealth(BaseModel):
    """Track system performance and health metrics."""

    response_time = models.FloatField(help_text="Average response time in seconds")
    cpu_usage = models.FloatField(null=True, blank=True, help_text="CPU usage percentage")
    memory_usage = models.FloatField(null=True, blank=True, help_text="Memory usage percentage")
    disk_usage = models.FloatField(null=True, blank=True, help_text="Disk usage percentage")

    # Error tracking
    error_count = models.PositiveIntegerField(default=0, help_text="Number of errors in the last hour")
    last_error = models.TextField(blank=True, help_text="Last error message")

    # Database stats
    db_connections = models.PositiveIntegerField(default=0, help_text="Active database connections")
    db_query_count = models.PositiveIntegerField(default=0, help_text="Queries executed")

    checked_at = models.DateTimeField(default=timezone.now, help_text="When this health check was performed")

    class Meta:
        verbose_name = "System Health"
        verbose_name_plural = "System Health"
        ordering = ['-checked_at']
        get_latest_by = 'checked_at'
