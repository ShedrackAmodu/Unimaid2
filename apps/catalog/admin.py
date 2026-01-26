from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from import_export.forms import ImportForm
from .models import Author, Publisher, Faculty, Department, Topic, Genre, Book, BookCopy
from .forms import AuthorForm, PublisherForm, FacultyForm, DepartmentForm, TopicForm, GenreForm, BookForm, BookCopyForm
from config.bulk_actions import (
    bulk_update_book_status, bulk_update_book_condition, bulk_update_book_location,
    bulk_assign_authors, bulk_assign_topics
)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    form = AuthorForm
    list_display = ['name', 'bio', 'book_count']
    search_fields = ['name']
    list_filter = ['books__faculty', 'books__department']

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    form = PublisherForm
    list_display = ['name', 'website', 'book_count']
    search_fields = ['name']
    list_filter = ['books__faculty', 'books__department']

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    form = FacultyForm
    list_display = ['name', 'code', 'description', 'department_count', 'book_count']
    search_fields = ['name', 'code']
    list_filter = []

    def department_count(self, obj):
        return obj.departments.count()
    department_count.short_description = 'Departments'

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    form = DepartmentForm
    list_display = ['name', 'code', 'faculty', 'topic_count', 'book_count']
    list_filter = ['faculty']
    search_fields = ['name', 'code']

    def topic_count(self, obj):
        return obj.topics.count()
    topic_count.short_description = 'Topics'

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    form = TopicForm
    list_display = ['name', 'code', 'department', 'faculty', 'book_count']
    list_filter = ['department__faculty', 'department']
    search_fields = ['name', 'code']

    def faculty(self, obj):
        return obj.department.faculty if obj.department else None
    faculty.short_description = 'Faculty'

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    form = GenreForm
    list_display = ['name', 'description', 'book_count']
    search_fields = ['name']

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


class BookResource(resources.ModelResource):
    authors = Field(attribute='authors', widget=ManyToManyWidget(Author, separator=', ', field='name'))

    class Meta:
        model = Book
        fields = ('id', 'title', 'isbn', 'authors', 'publisher__name', 'faculty__name', 'department__name', 'topic__name', 'genre__name', 'description', 'publication_date', 'edition', 'pages', 'language')
        export_order = fields
        import_id_fields = ['isbn']  # Use ISBN as unique identifier for imports
        skip_unchanged = True  # Skip rows that haven't changed
        report_skipped = True  # Report skipped rows
        chunk_size = 100  # Process in batches of 100

    def before_import_row(self, row, **kwargs):
        # Clean and validate data
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = value.strip()

        # Create related objects if they don't exist
        publisher_name = row.get('publisher__name')
        if publisher_name:
            publisher, created = Publisher.objects.get_or_create(
                name=publisher_name,
                defaults={'name': publisher_name}
            )
            row['publisher'] = publisher.id

        faculty_name = row.get('faculty__name')
        if faculty_name:
            faculty, created = Faculty.objects.get_or_create(
                name=faculty_name,
                defaults={'name': faculty_name, 'code': faculty_name[:10].upper()}
            )
            row['faculty'] = faculty.id

        department_name = row.get('department__name')
        if department_name:
            department, created = Department.objects.get_or_create(
                name=department_name,
                defaults={'name': department_name, 'code': department_name[:10].upper()}
            )
            row['department'] = department.id

        topic_name = row.get('topic__name')
        if topic_name:
            topic, created = Topic.objects.get_or_create(
                name=topic_name,
                defaults={'name': topic_name, 'code': topic_name[:20].upper()}
            )
            row['topic'] = topic.id

        genre_name = row.get('genre__name')
        if genre_name:
            genre, created = Genre.objects.get_or_create(
                name=genre_name,
                defaults={'name': genre_name}
            )
            row['genre'] = genre.id

        # Handle authors (many-to-many)
        authors_str = row.get('authors')
        if authors_str:
            author_names = [name.strip() for name in authors_str.split(',') if name.strip()]
            for author_name in author_names:
                Author.objects.get_or_create(name=author_name)




@admin.register(Book)
class BookAdmin(ImportExportModelAdmin):
    resource_class = BookResource
    form = BookForm
    list_display = ['title', 'isbn', 'publisher', 'faculty', 'department', 'topic', 'genre', 'publication_date', 'copy_count', 'available_copies']
    list_filter = ['faculty', 'department', 'topic__department__faculty', 'topic__department', 'topic', 'genre', 'publisher', 'publication_date']
    search_fields = ['title', 'isbn', 'authors__name']
    filter_horizontal = ['authors']
    readonly_fields = ['copy_count', 'available_copies']
    actions = ['bulk_upload_books']
    change_list_template = 'admin/catalog/book/change_list.html'



    def copy_count(self, obj):
        return obj.copies.count()
    copy_count.short_description = 'Total Copies'

    def available_copies(self, obj):
        return obj.copies.filter(status='available').count()
    available_copies.short_description = 'Available Copies'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add JavaScript for dynamic filtering
        if 'faculty' in form.base_fields:
            form.base_fields['faculty'].widget.attrs.update({
                'onchange': 'filterDepartments(this.value)',
                'data-url': reverse('admin:catalog_department_changelist')
            })
        if 'department' in form.base_fields:
            form.base_fields['department'].widget.attrs.update({
                'onchange': 'filterTopics(this.value)',
                'data-url': reverse('admin:catalog_topic_changelist')
            })
        return form

    class Media:
        js = ('admin/js/dynamic_filters.js',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_file_upload_view), name='catalog_book_bulk_upload'),
        ]
        return custom_urls + urls

    def bulk_file_upload_view(self, request):
        """Custom view for bulk uploading book files."""
        if request.method == 'POST':
            book_files = request.FILES.getlist('book_files')
            if not book_files:
                messages.error(request, 'Please select at least one book file to upload.')
                return redirect('admin:catalog_book_bulk_upload')

            # Get or create a default publisher for bulk books
            default_publisher, created = Publisher.objects.get_or_create(
                name='Bulk Upload Publisher',
                defaults={'name': 'Bulk Upload Publisher'}
            )

            uploaded_count = 0
            errors = []

            for file in book_files:
                try:
                    # Extract title from filename (remove extension)
                    filename = file.name
                    title = filename.rsplit('.', 1)[0] if '.' in filename else filename

                    # Generate a unique ISBN for bulk uploads
                    import uuid
                    isbn = f'BULK{str(uuid.uuid4())[:8].upper()}'

                    # Create book record
                    book = Book.objects.create(
                        title=title,
                        isbn=isbn,
                        publisher=default_publisher,
                        pages=1,  # Will be updated later
                        language='English',
                        publication_date='2024-01-01',
                        book_file=file
                    )

                    uploaded_count += 1

                except Exception as e:
                    errors.append(f'Failed to upload {file.name}: {str(e)}')

            # Report results
            if uploaded_count > 0:
                messages.success(request, f'Successfully uploaded {uploaded_count} book files.')

            if errors:
                for error in errors:
                    messages.error(request, error)

            return redirect('admin:catalog_book_changelist')

        context = {
            'title': 'Bulk Upload Book Files',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }

        return render(request, 'admin/catalog/book/bulk_upload.html', context)

    def bulk_upload_books(self, request, queryset):
        """Admin action to redirect to bulk upload page."""
        return HttpResponseRedirect(reverse('admin:catalog_book_bulk_upload'))
    bulk_upload_books.short_description = 'Bulk upload book files'


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    form = BookCopyForm
    list_display = ['book', 'barcode', 'status', 'condition', 'location', 'acquisition_date']
    list_filter = ['status', 'condition', 'book__faculty', 'book__department']
    search_fields = ['barcode', 'book__title']
    actions = ['mark_as_available', bulk_update_book_status, bulk_update_book_condition, bulk_update_book_location]



    def mark_as_available(self, request, queryset):
        updated = queryset.update(status='available')
        self.message_user(request, f'{updated} book copies marked as available.')
    mark_as_available.short_description = 'Mark selected copies as available'
