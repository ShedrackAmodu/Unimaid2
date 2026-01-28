from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, F, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Book, Author, Publisher, Faculty, Department, Topic, Genre, BookCopy
from .forms import BookForm, FacultyForm, DepartmentForm, TopicForm


class BookListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'books'
    paginate_by = 20

    def get_queryset(self):
        queryset = Book.objects.active().prefetch_related('authors', 'publisher', 'faculty', 'department', 'topic', 'genre')
        search_query = self.request.GET.get('q')
        topic_filter = self.request.GET.get('topic')
        faculty_filter = self.request.GET.get('faculty')
        department_filter = self.request.GET.get('department')
        genre_filter = self.request.GET.get('genre')
        author_filter = self.request.GET.get('author')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(authors__name__icontains=search_query) |
                Q(isbn__icontains=search_query) |
                Q(description__icontains=search_query)
            ).distinct()

        if topic_filter:
            queryset = queryset.filter(topic_id=topic_filter)

        if faculty_filter:
            queryset = queryset.filter(
                Q(faculty_id=faculty_filter) |
                Q(topic__department__faculty_id=faculty_filter)
            ).distinct()

        if department_filter:
            queryset = queryset.filter(
                Q(department_id=department_filter) |
                Q(topic__department_id=department_filter)
            ).distinct()

        if genre_filter:
            try:
                genre_id = int(genre_filter)
                queryset = queryset.filter(genre_id=genre_id)
            except ValueError:
                queryset = queryset.filter(genre__name=genre_filter)

        if author_filter:
            queryset = queryset.filter(authors__id=author_filter)

        return queryset.order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faculties'] = Faculty.objects.prefetch_related('departments__topics').all()
        context['departments'] = Department.objects.select_related('faculty').all()
        context['topics'] = Topic.objects.select_related('department__faculty').all()
        context['genres'] = Genre.objects.all()
        context['authors'] = Author.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_topic'] = self.request.GET.get('topic', '')
        context['selected_faculty'] = self.request.GET.get('faculty', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_genre'] = self.request.GET.get('genre', '')
        context['selected_author'] = self.request.GET.get('author', '')
        
        # Calculate dynamic statistics
        total_books = Book.objects.active().count()
        available_books = Book.objects.active().filter(copies__status='available').distinct().count()
        genres_count = Genre.objects.filter(books__isnull=False).distinct().count()
        authors_count = Author.objects.filter(books__isnull=False).distinct().count()
        
        context['total_books'] = total_books
        context['available_books'] = available_books
        context['genres_count'] = genres_count
        context['authors_count'] = authors_count
        
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
        queryset = Author.objects.prefetch_related('books').order_by('name')
        search_query = self.request.GET.get('q')
        letter_filter = self.request.GET.get('letter')
        sort_by = self.request.GET.get('sort', 'name')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(bio__icontains=search_query)
            )

        if letter_filter:
            if letter_filter == '0-9':
                queryset = queryset.filter(name__regex=r'^[0-9]')
            else:
                queryset = queryset.filter(name__istartswith=letter_filter)

        if sort_by == 'popular':
            queryset = queryset.annotate(book_count=Count('books')).order_by('-book_count', 'name')
        elif sort_by == 'books':
            queryset = queryset.annotate(book_count=Count('books')).order_by('-book_count', 'name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at', 'name')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basic statistics
        total_authors = Author.objects.count()
        total_books = Book.objects.active().count()
        avg_books_per_author = round(total_books / total_authors, 1) if total_authors > 0 else 0

        # Featured authors (top by book count)
        featured_authors = Author.objects.annotate(
            book_count=Count('books')
        ).order_by('-book_count', 'name')[:4]

        # Alphabet for filtering
        alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Search query
        search_query = self.request.GET.get('q', '')

        # Genre statistics for progress bars (top 3 genres by author count)
        top_genres = Genre.objects.annotate(
            author_count=Count('books__authors', distinct=True)
        ).filter(author_count__gt=0).order_by('-author_count')[:3]

        # All genres with author counts for category links
        genre_stats = Genre.objects.annotate(
            author_count=Count('books__authors', distinct=True)
        ).filter(author_count__gt=0).order_by('-author_count')[:5]

        context.update({
            'total_authors': total_authors,
            'total_books': total_books,
            'avg_books_per_author': avg_books_per_author,
            'featured_authors': featured_authors,
            'alphabet': alphabet,
            'search_query': search_query,
            'top_genres': top_genres,
            'genre_stats': genre_stats,
        })

        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basic statistics
        total_publishers = Publisher.objects.count()
        total_books = Book.objects.active().count()
        avg_books_per_publisher = round(total_books / total_publishers, 1) if total_publishers > 0 else 0

        # Featured publishers (top by book count)
        featured_publishers = Publisher.objects.annotate(
            book_count=Count('books')
        ).order_by('-book_count', 'name')[:4]

        context.update({
            'total_publishers': total_publishers,
            'total_books': total_books,
            'avg_books_per_publisher': avg_books_per_publisher,
            'featured_publishers': featured_publishers,
        })

        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basic statistics
        total_genres = Genre.objects.count()
        total_books = Book.objects.active().count()
        avg_books_per_genre = round(total_books / total_genres, 1) if total_genres > 0 else 0

        # Popular genres (top by book count)
        popular_genres = Genre.objects.annotate(
            book_count=Count('books')
        ).order_by('-book_count', 'name')[:6]

        # Alphabet for filtering
        alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Discover genres (other genres with fewer books)
        discover_genres = Genre.objects.annotate(
            book_count=Count('books')
        ).filter(book_count__gt=0).order_by('?')[:3]

        context.update({
            'total_genres': total_genres,
            'total_books': total_books,
            'avg_books_per_genre': avg_books_per_genre,
            'popular_genres': popular_genres,
            'alphabet': alphabet,
            'discover_genres': discover_genres,
        })

        return context


class GenreDetailView(DetailView):
    model = Genre
    template_name = 'catalog/genre_detail.html'
    context_object_name = 'genre'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        genre = self.get_object()
        context['books'] = genre.books.active().prefetch_related('authors', 'publisher')
        return context


class FacultyListView(ListView):
    model = Faculty
    template_name = 'catalog/faculty_list.html'
    context_object_name = 'faculties'
    paginate_by = 20

    def get_queryset(self):
        return Faculty.objects.prefetch_related('departments__topics').order_by('name')


class FacultyDetailView(DetailView):
    model = Faculty
    template_name = 'catalog/faculty_detail.html'
    context_object_name = 'faculty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.get_object()
        context['departments'] = faculty.departments.prefetch_related('topics').order_by('name')
        context['available_books'] = sum(dept.books.filter(bookcopy__status='available').distinct().count() for dept in faculty.departments.all()) or faculty.books.filter(bookcopy__status='available').distinct().count()

        # Get top genres in this faculty
        context['top_genres'] = faculty.books.values('genre__name').annotate(
            count=Count('genre')
        ).filter(genre__name__isnull=False).order_by('-count')[:5]

        # Get related faculties (other faculties with books)
        context['related_faculties'] = Faculty.objects.exclude(id=faculty.id).filter(
            books__isnull=False
        ).distinct().order_by('name')[:4]

        return context


class DepartmentListView(ListView):
    model = Department
    template_name = 'catalog/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20

    def get_queryset(self):
        return Department.objects.select_related('faculty').prefetch_related('topics').order_by('faculty__name', 'name')


class DepartmentDetailView(DetailView):
    model = Department
    template_name = 'catalog/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department = self.get_object()
        context['topics'] = department.topics.order_by('name')

        # Calculate available books
        context['available_books'] = department.books.filter(bookcopy__status='available').distinct().count()

        # Get top genres in this department
        context['top_genres'] = department.books.values('genre__name').annotate(
            count=Count('genre')
        ).filter(genre__name__isnull=False).order_by('-count')[:5]

        # Get related departments (other departments in same faculty)
        context['related_departments'] = Department.objects.filter(
            faculty=department.faculty
        ).exclude(id=department.id).order_by('name')[:4]

        return context


class TopicListView(ListView):
    model = Topic
    template_name = 'catalog/topic_list.html'
    context_object_name = 'topics'
    paginate_by = 20

    def get_queryset(self):
        return Topic.objects.select_related('department__faculty').order_by('department__faculty__name', 'department__name', 'name')


class TopicDetailView(DetailView):
    model = Topic
    template_name = 'catalog/topic_detail.html'
    context_object_name = 'topic'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.get_object()
        context['books'] = topic.books.active().prefetch_related('authors', 'publisher', 'genre')

        # Calculate available books
        context['available_books'] = topic.books.filter(bookcopy__status='available').distinct().count()

        # Get publication timeline data
        context['publication_years'] = topic.books.values('publication_date__year').annotate(
            count=Count('id'),
            year=F('publication_date__year')
        ).filter(publication_date__year__isnull=False).order_by('-year')[:6]

        # Get top genres in this topic
        context['top_genres'] = topic.books.values('genre__name').annotate(
            count=Count('genre')
        ).filter(genre__name__isnull=False).order_by('-count')[:5]

        # Get related topics (other topics in same department)
        context['related_topics'] = Topic.objects.filter(
            department=topic.department
        ).exclude(id=topic.id).order_by('name')[:4]

        # Recent books count (books added in last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context['recent_books'] = topic.books.filter(created_at__gte=thirty_days_ago).count()

        return context


def home_view(request):
    """Catalog home page showing faculties, departments, and featured books."""
    # Prioritize faculty/department hierarchy as the primary navigation
    faculties = Faculty.objects.prefetch_related('departments__topics').order_by('name')
    departments = Department.objects.select_related('faculty').prefetch_related('topics').order_by('faculty__name', 'name')[:12]  # Show more departments
    topics = Topic.objects.select_related('department__faculty').order_by('department__faculty__name', 'department__name', 'name')[:8]

    # Get featured books with faculty/department context
    featured_books = Book.objects.active().prefetch_related('authors', 'faculty', 'department', 'topic', 'genre')[:6]
    recent_books = Book.objects.active().order_by('-created_at').prefetch_related('faculty', 'department', 'topic')[:6]

    # Statistics for the home page
    total_books = Book.objects.active().count()
    total_faculties = faculties.count()
    total_departments = Department.objects.count()
    total_topics = Topic.objects.count()

    context = {
        'faculties': faculties,
        'departments': departments,
        'topics': topics,
        'featured_books': featured_books,
        'recent_books': recent_books,
        'total_books': total_books,
        'total_faculties': total_faculties,
        'total_departments': total_departments,
        'total_topics': total_topics,
    }
    return render(request, 'catalog/home.html', context)


@staff_member_required
def admin_book_upload(request):
    """Admin view for uploading books with proper category linking."""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" has been successfully added to the catalog.')
            return redirect('admin:catalog_book_changelist')
    else:
        form = BookForm()

    context = {
        'form': form,
        'title': 'Upload New Book',
        'opts': Book._meta,
    }
    return render(request, 'admin/catalog/book/upload.html', context)


@staff_member_required
def admin_faculty_create(request):
    """Admin view for creating faculties."""
    if request.method == 'POST':
        form = FacultyForm(request.POST)
        if form.is_valid():
            faculty = form.save()
            messages.success(request, f'Faculty "{faculty.name}" has been successfully created.')
            return redirect('admin:catalog_faculty_changelist')
    else:
        form = FacultyForm()

    context = {
        'form': form,
        'title': 'Create New Faculty',
        'opts': Faculty._meta,
    }
    return render(request, 'admin/catalog/faculty/create.html', context)


@staff_member_required
def admin_department_create(request):
    """Admin view for creating departments."""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department "{department.name}" has been successfully created.')
            return redirect('admin:catalog_department_changelist')
    else:
        form = DepartmentForm()

    context = {
        'form': form,
        'title': 'Create New Department',
        'opts': Department._meta,
    }
    return render(request, 'admin/catalog/department/create.html', context)


@staff_member_required
def admin_topic_create(request):
    """Admin view for creating topics."""
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save()
            messages.success(request, f'Topic "{topic.name}" has been successfully created.')
            return redirect('admin:catalog_topic_changelist')
    else:
        form = TopicForm()

    context = {
        'form': form,
        'title': 'Create New Topic',
        'opts': Topic._meta,
    }
    return render(request, 'admin/catalog/topic/create.html', context)


def api_departments(request):
    """API endpoint to get departments, optionally filtered by faculty."""
    faculty_id = request.GET.get('faculty')
    if faculty_id:
        departments = Department.objects.filter(faculty_id=faculty_id).values('id', 'name')
    else:
        departments = Department.objects.values('id', 'name')
    return JsonResponse(list(departments), safe=False)


def api_topics(request):
    """API endpoint to get topics, optionally filtered by department."""
    department_id = request.GET.get('department')
    if department_id:
        topics = Topic.objects.filter(department_id=department_id).values('id', 'name')
    else:
        topics = Topic.objects.values('id', 'name')
    return JsonResponse(list(topics), safe=False)


def download_book_qr(request, book_id):
    """Download QR code for a book."""
    book = get_object_or_404(Book, id=book_id)
    if not book.qr_code:
        # Generate QR code if it doesn't exist
        book.generate_qr_code()
        book.save()

    # Return the QR code file
    response = HttpResponse(book.qr_code, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="book_{book.id}_qr.png"'
    return response


def download_copy_qr(request, copy_id):
    """Download QR code for a book copy."""
    copy = get_object_or_404(BookCopy, id=copy_id)
    if not copy.qr_code:
        # Generate QR code if it doesn't exist
        copy.generate_qr_code()
        copy.save()

    # Return the QR code file
    response = HttpResponse(copy.qr_code, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="copy_{copy.id}_qr.png"'
    return response
