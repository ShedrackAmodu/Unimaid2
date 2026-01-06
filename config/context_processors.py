from django.contrib.auth.models import ContentType
from django.db.models import Count
from apps.accounts.models import LibraryUser
from apps.catalog.models import Book, BookCopy
from apps.repository.models import Document
from apps.events.models import Event
from apps.circulation.models import Loan
from django.utils import timezone


def admin_context(request):
    """Custom context processor for admin panel."""
    context = {}

    if request.user.is_staff and request.path.startswith('/admin/'):
        # Get statistics
        context.update({
            'user_count': LibraryUser.objects.count(),
            'book_count': Book.objects.count(),
            'document_count': Document.objects.count(),
            'event_count': Event.objects.filter(date__gte=timezone.now().date()).count(),
            'active_users': LibraryUser.objects.filter(is_active=True).count(),
            'overdue_loans': Loan.objects.filter(
                status='active',
                due_date__lt=timezone.now()
            ).count(),
            'pending_reservations': 0,  # Add your reservation model count
        })

        # Customize app list with icons
        app_icons = {
            'accounts': 'people',
            'catalog': 'book',
            'circulation': 'arrow-left-right',
            'repository': 'archive',
            'blog': 'newspaper',
            'events': 'calendar-event',
        }

        model_icons = {
            'libraryuser': 'person',
            'book': 'book',
            'bookcopy': 'book-half',
            'author': 'person-badge',
            'publisher': 'building',
            'genre': 'tag',
            'loan': 'arrow-left-right',
            'reservation': 'bookmark',
            'fine': 'cash-coin',
            'document': 'file-earmark-text',
            'collection': 'folder',
            'blogpost': 'newspaper',
            'event': 'calendar-event',
            'eventregistration': 'calendar-check',
        }

    return context
