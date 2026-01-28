from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Q
from .models import Collection, EBook, EBookPermissionRequest, EBookPermission
from .serializers import (
    CollectionSerializer, EBookSerializer, EBookPermissionRequestSerializer,
    EBookPermissionSerializer, EBookSearchSerializer
)


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for Collection model."""
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Collection.objects.all()
        curator = self.request.query_params.get('curator', None)

        if curator:
            queryset = queryset.filter(curator_id=curator)

        return queryset


class EBookViewSet(viewsets.ModelViewSet):
    """ViewSet for EBook model."""
    queryset = EBook.objects.all()
    serializer_class = EBookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = EBook.objects.all()
        user = self.request.user
        search_serializer = EBookSearchSerializer(data=self.request.query_params)
        search_serializer.is_valid(raise_exception=False)

        if search_serializer.validated_data:
            params = search_serializer.validated_data

            # Enhanced search across multiple fields
            if params.get('q'):
                search_term = params['q']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(authors__icontains=search_term) |
                    Q(abstract__icontains=search_term) |
                    Q(doi__icontains=search_term) |
                    Q(collection__name__icontains=search_term)
                ).distinct()

            if params.get('title'):
                queryset = queryset.filter(title__icontains=params['title'])

            if params.get('authors'):
                queryset = queryset.filter(authors__icontains=params['authors'])

            if params.get('collection'):
                queryset = queryset.filter(collection__name__icontains=params['collection'])

            if params.get('access_level'):
                queryset = queryset.filter(access_level=params['access_level'])

            if params.get('uploaded_by'):
                queryset = queryset.filter(uploaded_by__username__icontains=params['uploaded_by'])

            if params.get('date_from'):
                queryset = queryset.filter(upload_date__date__gte=params['date_from'])

            if params.get('date_to'):
                queryset = queryset.filter(upload_date__date__lte=params['date_to'])

        # Filter by user access permissions for non-open documents
        if user.is_authenticated:
            # Users can see open documents and documents they have permission to access
            accessible_docs = Q(access_level='open') | Q(
                access_level__in=['restricted', 'embargo', 'private'],
                permissions__user=user,
                permissions__granted=True
            )
            queryset = queryset.filter(accessible_docs).distinct()
        else:
            # Anonymous users can only see open documents
            queryset = queryset.filter(access_level='open')

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def download(self, request, pk=None):
        """Track document download."""
        ebook = self.get_object()

        # Check if user can access this document
        if not ebook.can_user_access(request.user):
            return Response(
                {'error': 'You do not have permission to access this document'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Track the download event
        from apps.analytics.models import AnalyticsEvent
        AnalyticsEvent.objects.create(
            event_type='download',
            user=request.user,
            document=ebook,
            session_id=request.session.session_key,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            page_url=request.META.get('HTTP_REFERER'),
        )

        # Update popularity score
        from apps.analytics.models import PopularItem
        popular_item, created = PopularItem.objects.get_or_create(
            item_type='document',
            document=ebook,
            defaults={'checkout_count': 0, 'view_count': 0, 'search_count': 0}
        )
        popular_item.checkout_count += 1
        popular_item.update_score()

        return Response({
            'message': 'Download recorded',
            'download_url': ebook.file.url if ebook.file else None
        })


class EBookPermissionRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for EBookPermissionRequest model."""
    queryset = EBookPermissionRequest.objects.all()
    serializer_class = EBookPermissionRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EBookPermissionRequest.objects.all()
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


class EBookPermissionViewSet(viewsets.ModelViewSet):
    """ViewSet for EBookPermission model."""
    queryset = EBookPermission.objects.all()
    serializer_class = EBookPermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EBookPermission.objects.all()
        user = self.request.user
        ebook = self.request.query_params.get('ebook', None)

        # Regular users can only see permissions for documents they uploaded
        if not user.is_staff:
            queryset = queryset.filter(ebook__uploaded_by=user)

        if ebook:
            queryset = queryset.filter(ebook_id=ebook)

        return queryset

    def perform_create(self, serializer):
        # Only staff can grant permissions
        if not self.request.user.is_staff:
            raise PermissionError("Only staff can grant document permissions")
        serializer.save(granted_by=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    """Global search across books and documents."""
    query = request.query_params.get('q', '')
    limit = request.query_params.get('limit', 20)

    try:
        limit = int(limit)
    except ValueError:
        limit = 20

    if not query or len(query) < 2:
        return Response({
            'books': [],
            'documents': [],
            'total_books': 0,
            'total_documents': 0
        })

    # Search books
    from apps.catalog.models import Book
    from apps.catalog.serializers import BookSerializer

    books_queryset = Book.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(authors__name__icontains=query) |
        Q(isbn__icontains=query) |
        Q(publisher__name__icontains=query) |
        Q(genre__name__icontains=query)
    ).distinct()[:limit//2]

    books_data = BookSerializer(books_queryset, many=True, context={'request': request}).data

    # Search documents (respecting access permissions)
    documents_queryset = EBook.objects.filter(
        Q(title__icontains=query) |
        Q(authors__icontains=query) |
        Q(abstract__icontains=query) |
        Q(collection__name__icontains=query)
    ).distinct()

    # Apply access filtering
    user = request.user
    if user.is_authenticated:
        accessible_docs = Q(access_level='open') | Q(
            access_level__in=['restricted', 'embargo', 'private'],
            permissions__user=user,
            permissions__granted=True
        )
        documents_queryset = documents_queryset.filter(accessible_docs).distinct()
    else:
        documents_queryset = documents_queryset.filter(access_level='open')

    documents_queryset = documents_queryset[:limit//2]
    documents_data = EBookSerializer(documents_queryset, many=True, context={'request': request}).data

    # Track search event
    from apps.analytics.models import AnalyticsEvent
    AnalyticsEvent.objects.create(
        event_type='search',
        user=user if user.is_authenticated else None,
        session_id=request.session.session_key,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        search_query=query,
        metadata={'results_count': len(books_data) + len(documents_data)}
    )

    return Response({
        'query': query,
        'books': books_data,
        'documents': documents_data,
        'total_books': len(books_data),
        'total_documents': len(documents_data),
        'total_results': len(books_data) + len(documents_data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_suggestions(request):
    """Get global search suggestions."""
    query = request.query_params.get('q', '')
    if len(query) < 2:
        return Response([])

    suggestions = []

    # Book title suggestions
    from apps.catalog.models import Book
    book_titles = Book.objects.filter(
        title__icontains=query
    ).values_list('title', flat=True).distinct()[:5]
    suggestions.extend([{'type': 'book', 'value': title} for title in book_titles])

    # Author suggestions
    from apps.catalog.models import Author
    authors = Author.objects.filter(
        name__icontains=query
    ).values_list('name', flat=True).distinct()[:5]
    suggestions.extend([{'type': 'author', 'value': author} for author in authors])

    # Document title suggestions
    document_titles = EBook.objects.filter(
        title__icontains=query
    ).values_list('title', flat=True).distinct()[:5]
    suggestions.extend([{'type': 'document', 'value': title} for title in document_titles])

    return Response(suggestions[:10])
