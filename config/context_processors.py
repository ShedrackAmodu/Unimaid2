from django.contrib.auth.models import ContentType
from django.db.models import Count, Sum
from django.core.cache import cache
from apps.accounts.models import LibraryUser
from apps.catalog.models import Book, BookCopy, Faculty, Department, Topic
from apps.repository.models import EBook
from apps.events.models import Event
from apps.circulation.models import Loan, Reservation, Fine
from django.utils import timezone


def library_counts(request):
    """Context processor for library-wide statistics and counts."""
    context = {}
    
    # Cache key for library statistics
    cache_key = 'library_stats'
    stats = cache.get(cache_key)
    
    if not stats:
        # Calculate statistics with optimized queries
        stats = {
            'total_users': LibraryUser.objects.count(),
            'total_books': Book.objects.active().count(),
            'total_documents': EBook.objects.count(),
            'total_faculties': Faculty.objects.count(),
            'total_departments': Department.objects.count(),
            'total_topics': Topic.objects.count(),
            'active_loans': Loan.objects.filter(status='active').count(),
            'overdue_loans': Loan.objects.filter(status='active', due_date__lt=timezone.now()).count(),
            'pending_reservations': Reservation.objects.filter(status='active').count(),
            'total_events': Event.objects.filter(date__gte=timezone.now().date()).count(),
        }
        
        # Cache for 5 minutes to improve performance
        cache.set(cache_key, stats, 300)
    
    context.update(stats)
    
    # Add user-specific counts if authenticated
    if request.user.is_authenticated:
        user_stats = cache.get(f'user_stats_{request.user.id}')
        
        if not user_stats:
            user_stats = {
                'user_current_loans': request.user.loans.filter(status='active').count(),
                'user_overdue_loans': request.user.loans.filter(
                    status='active', 
                    due_date__lt=timezone.now()
                ).count(),
                'user_active_reservations': request.user.reservations.filter(status='active').count(),
                'user_pending_requests': request.user.loan_requests.filter(status='pending').count(),
                'user_unpaid_fines': Fine.objects.filter(
                    loan__user=request.user, 
                    status='unpaid'
                ).aggregate(total=Sum('amount'))['total'] or 0,
            }
            
            # Cache user stats for 2 minutes
            cache.set(f'user_stats_{request.user.id}', user_stats, 120)
        
        context.update(user_stats)
    
    return context


def admin_context(request):
    """Custom context processor for admin panel."""
    context = {}

    if request.user.is_staff and request.path.startswith('/admin/'):
        # Get statistics
        context.update({
            'user_count': LibraryUser.objects.count(),
            'book_count': Book.objects.count(),
            'document_count': EBook.objects.count(),
            'event_count': Event.objects.filter(date__gte=timezone.now().date()).count(),
            'active_users': LibraryUser.objects.filter(is_active=True).count(),
            'overdue_loans': Loan.objects.filter(
                status='active',
                due_date__lt=timezone.now()
            ).count(),
            'pending_reservations': Reservation.objects.filter(status='active').count(),
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
            'ebook': 'file-earmark-text',
            'collection': 'folder',
            'blogpost': 'newspaper',
            'event': 'calendar-event',
            'eventregistration': 'calendar-check',
        }

    return context
