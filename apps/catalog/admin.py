from django.contrib import admin
from .models import Author, Publisher, Genre, Book, BookCopy


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'bio']
    search_fields = ['name']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'website']
    search_fields = ['name']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'isbn', 'publisher', 'genre', 'publication_date']
    list_filter = ['genre', 'publisher', 'publication_date']
    search_fields = ['title', 'isbn']
    filter_horizontal = ['authors']


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ['book', 'barcode', 'status', 'condition', 'location']
    list_filter = ['status', 'condition']
    search_fields = ['barcode', 'book__title']
    actions = ['mark_as_available']

    def mark_as_available(self, request, queryset):
        updated = queryset.update(status='available')
        self.message_user(request, f'{updated} book copies marked as available.')
    mark_as_available.short_description = 'Mark selected copies as available'
