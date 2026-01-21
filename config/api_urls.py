from django.urls import path, include
from rest_framework import routers

# Import API views
from apps.accounts.api import (
    LibraryUserViewSet, StudyRoomViewSet, StudyRoomBookingViewSet,
    login, logout, register
)
from apps.catalog.api import (
    AuthorViewSet, PublisherViewSet, FacultyViewSet, DepartmentViewSet,
    TopicViewSet, GenreViewSet, BookViewSet, BookCopyViewSet
)
from apps.circulation.api import (
    LoanViewSet, ReservationViewSet, LoanRequestViewSet, FineViewSet,
    AttendanceViewSet, checkout_book, return_book
)
from apps.analytics.api import (
    AnalyticsEventViewSet, DailyStatsViewSet, PopularItemViewSet,
    SystemHealthViewSet, track_event, dashboard, update_daily_stats
)
from apps.repository.api import (
    CollectionViewSet, DocumentViewSet, DocumentPermissionRequestViewSet,
    DocumentPermissionViewSet, global_search, search_suggestions
)

# Create routers
accounts_router = routers.DefaultRouter()
accounts_router.register(r'users', LibraryUserViewSet)
accounts_router.register(r'study-rooms', StudyRoomViewSet)
accounts_router.register(r'study-room-bookings', StudyRoomBookingViewSet)

catalog_router = routers.DefaultRouter()
catalog_router.register(r'authors', AuthorViewSet)
catalog_router.register(r'publishers', PublisherViewSet)
catalog_router.register(r'faculties', FacultyViewSet)
catalog_router.register(r'departments', DepartmentViewSet)
catalog_router.register(r'topics', TopicViewSet)
catalog_router.register(r'genres', GenreViewSet)
catalog_router.register(r'books', BookViewSet)
catalog_router.register(r'book-copies', BookCopyViewSet)

circulation_router = routers.DefaultRouter()
circulation_router.register(r'loans', LoanViewSet)
circulation_router.register(r'reservations', ReservationViewSet)
circulation_router.register(r'loan-requests', LoanRequestViewSet)
circulation_router.register(r'fines', FineViewSet)
circulation_router.register(r'attendance', AttendanceViewSet)

analytics_router = routers.DefaultRouter()
analytics_router.register(r'events', AnalyticsEventViewSet)
analytics_router.register(r'daily-stats', DailyStatsViewSet)
analytics_router.register(r'popular-items', PopularItemViewSet)
analytics_router.register(r'system-health', SystemHealthViewSet)

repository_router = routers.DefaultRouter()
repository_router.register(r'collections', CollectionViewSet)
repository_router.register(r'documents', DocumentViewSet)
repository_router.register(r'document-permissions', DocumentPermissionViewSet)
repository_router.register(r'permission-requests', DocumentPermissionRequestViewSet)

# URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login, name='api-login'),
    path('auth/logout/', logout, name='api-logout'),
    path('auth/register/', register, name='api-register'),

    # Circulation actions
    path('circulation/checkout/', checkout_book, name='api-checkout'),
    path('circulation/return/', return_book, name='api-return'),

    # Analytics endpoints
    path('analytics/track-event/', track_event, name='api-track-event'),
    path('analytics/dashboard/', dashboard, name='api-dashboard'),
    path('analytics/update-daily-stats/', update_daily_stats, name='api-update-daily-stats'),

    # Search endpoints
    path('search/', global_search, name='api-global-search'),
    path('search/suggestions/', search_suggestions, name='api-search-suggestions'),

    # Router URLs
    path('accounts/', include(accounts_router.urls)),
    path('catalog/', include(catalog_router.urls)),
    path('circulation/', include(circulation_router.urls)),
    path('analytics/', include(analytics_router.urls)),
    path('repository/', include(repository_router.urls)),
]
