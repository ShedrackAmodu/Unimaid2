from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Author, Publisher, Faculty, Department, Topic, Genre, Book, BookCopy
from .forms import AuthorForm, PublisherForm, FacultyForm, DepartmentForm, TopicForm, GenreForm, BookForm, BookCopyForm


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


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    form = BookForm
    list_display = ['title', 'isbn', 'publisher', 'faculty', 'department', 'topic', 'genre', 'publication_date', 'copy_count', 'available_copies']
    list_filter = ['faculty', 'department', 'topic__department__faculty', 'topic__department', 'topic', 'genre', 'publisher', 'publication_date']
    search_fields = ['title', 'isbn', 'authors__name']
    filter_horizontal = ['authors']
    readonly_fields = ['copy_count', 'available_copies']

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


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    form = BookCopyForm
    list_display = ['book', 'barcode', 'status', 'condition', 'location', 'acquisition_date']
    list_filter = ['status', 'condition', 'book__faculty', 'book__department']
    search_fields = ['barcode', 'book__title']
    actions = ['mark_as_available']

    def mark_as_available(self, request, queryset):
        updated = queryset.update(status='available')
        self.message_user(request, f'{updated} book copies marked as available.')
    mark_as_available.short_description = 'Mark selected copies as available'
