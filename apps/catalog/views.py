from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Book, Author, Publisher, Genre, BookCopy


class BookListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'books'
    paginate_by = 20

    def get_queryset(self):
        queryset = Book.objects.active().prefetch_related('authors', 'publisher', 'genre')
        search_query = self.request.GET.get('q')
        genre_filter = self.request.GET.get('genre')
        author_filter = self.request.GET.get('author')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(authors__name__icontains=search_query) |
                Q(isbn__icontains=search_query) |
                Q(description__icontains=search_query)
            ).distinct()

        if genre_filter:
            queryset = queryset.filter(genre_id=genre_filter)

        if author_filter:
            queryset = queryset.filter(authors__id=author_filter)

        return queryset.order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        context['authors'] = Author.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_genre'] = self.request.GET.get('genre', '')
        context['selected_author'] = self.request.GET.get('author', '')
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = 'catalog/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        context['available_copies'] = book.copies.available().count()
        context['total_copies'] = book.copies.count()
        context['is_available'] = book.is_available()
        return context


class AuthorListView(ListView):
    model = Author
    template_name = 'catalog/author_list.html'
    context_object_name = 'authors'
    paginate_by = 20

    def get_queryset(self):
        return Author.objects.prefetch_related('books').order_by('name')


class AuthorDetailView(DetailView):
    model = Author
    template_name = 'catalog/author_detail.html'
    context_object_name = 'author'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.get_object()
        context['books'] = author.books.active().prefetch_related('genre', 'publisher')
        return context


class PublisherListView(ListView):
    model = Publisher
    template_name = 'catalog/publisher_list.html'
    context_object_name = 'publishers'
    paginate_by = 20

    def get_queryset(self):
        return Publisher.objects.prefetch_related('books').order_by('name')


class PublisherDetailView(DetailView):
    model = Publisher
    template_name = 'catalog/publisher_detail.html'
    context_object_name = 'publisher'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publisher = self.get_object()
        context['books'] = publisher.books.active().prefetch_related('authors', 'genre')
        return context


class GenreListView(ListView):
    model = Genre
    template_name = 'catalog/genre_list.html'
    context_object_name = 'genres'
    paginate_by = 20

    def get_queryset(self):
        return Genre.objects.prefetch_related('books').order_by('name')


class GenreDetailView(DetailView):
    model = Genre
    template_name = 'catalog/genre_detail.html'
    context_object_name = 'genre'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        genre = self.get_object()
        context['books'] = genre.books.active().prefetch_related('authors', 'publisher')
        return context


def home_view(request):
    """Catalog home page showing featured books and quick search."""
    featured_books = Book.objects.active().prefetch_related('authors', 'genre')[:6]
    recent_books = Book.objects.active().order_by('-created_at')[:6]
    popular_genres = Genre.objects.prefetch_related('books')[:6]

    context = {
        'featured_books': featured_books,
        'recent_books': recent_books,
        'popular_genres': popular_genres,
    }
    return render(request, 'catalog/home.html', context)
