from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Q
from .models import Author, Publisher, Faculty, Department, Topic, Genre, Book, BookCopy
from .serializers import (
    AuthorSerializer, PublisherSerializer, FacultySerializer, DepartmentSerializer,
    TopicSerializer, GenreSerializer, BookSerializer, BookCopySerializer,
    BookSearchSerializer
)


class AuthorViewSet(viewsets.ModelViewSet):
    """ViewSet for Author model."""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class PublisherViewSet(viewsets.ModelViewSet):
    """ViewSet for Publisher model."""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class FacultyViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for Faculty model."""
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for Department model."""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for Topic model."""
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for Genre model."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class BookViewSet(viewsets.ModelViewSet):
    """ViewSet for Book model."""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Book.objects.all()
        search_serializer = BookSearchSerializer(data=self.request.query_params)
        search_serializer.is_valid(raise_exception=False)

        if search_serializer.validated_data:
            params = search_serializer.validated_data

            # Enhanced full-text search across multiple fields
            if params.get('q'):
                search_term = params['q']
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(authors__name__icontains=search_term) |
                    Q(isbn__icontains=search_term) |
                    Q(publisher__name__icontains=search_term) |
                    Q(genre__name__icontains=search_term) |
                    Q(faculty__name__icontains=search_term) |
                    Q(department__name__icontains=search_term) |
                    Q(language__icontains=search_term)
                ).distinct()

            # Individual field filters
            if params.get('author'):
                queryset = queryset.filter(authors__name__icontains=params['author'])

            if params.get('title'):
                queryset = queryset.filter(title__icontains=params['title'])

            if params.get('isbn'):
                queryset = queryset.filter(isbn__icontains=params['isbn'])

            if params.get('genre'):
                queryset = queryset.filter(genre__name__icontains=params['genre'])

            if params.get('publisher'):
                queryset = queryset.filter(publisher__name__icontains=params['publisher'])

            if params.get('faculty'):
                queryset = queryset.filter(faculty__name__icontains=params['faculty'])

            if params.get('department'):
                queryset = queryset.filter(department__name__icontains=params['department'])

            if params.get('language'):
                queryset = queryset.filter(language__icontains=params['language'])

            if params.get('available_only'):
                queryset = queryset.filter(copies__status='available').distinct()

        return queryset

    @action(detail=True, methods=['get'])
    def copies(self, request, pk=None):
        """Get all copies of a book."""
        book = self.get_object()
        copies = book.copies.all()
        serializer = BookCopySerializer(copies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """Get search suggestions."""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response([])

        # Get suggestions from various fields
        suggestions = []

        # Title suggestions
        titles = Book.objects.filter(
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:5]
        suggestions.extend([{'type': 'title', 'value': title} for title in titles])

        # Author suggestions
        authors = Author.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True).distinct()[:5]
        suggestions.extend([{'type': 'author', 'value': author} for author in authors])

        # Genre suggestions
        genres = Genre.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True).distinct()[:5]
        suggestions.extend([{'type': 'genre', 'value': genre} for genre in genres])

        return Response(suggestions[:10])


class BookCopyViewSet(viewsets.ModelViewSet):
    """ViewSet for BookCopy model."""
    queryset = BookCopy.objects.all()
    serializer_class = BookCopySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = BookCopy.objects.all()
        book_id = self.request.query_params.get('book', None)
        status_filter = self.request.query_params.get('status', None)
        available_only = self.request.query_params.get('available_only', None)

        if book_id:
            queryset = queryset.filter(book_id=book_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if available_only:
            queryset = queryset.filter(status='available')

        return queryset
