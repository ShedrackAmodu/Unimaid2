from rest_framework import serializers
from .models import Author, Publisher, Faculty, Department, Topic, Genre, Book, BookCopy


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author model."""

    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for Publisher model."""

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'address', 'website', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FacultySerializer(serializers.ModelSerializer):
    """Serializer for Faculty model."""

    class Meta:
        model = Faculty
        fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'code', 'faculty', 'faculty_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic model."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    faculty_name = serializers.CharField(source='department.faculty.name', read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'code', 'department', 'department_name', 'faculty_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for Genre model."""

    class Meta:
        model = Genre
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookSerializer(serializers.ModelSerializer):
    """Serializer for Book model."""
    authors = AuthorSerializer(many=True, read_only=True)
    authors_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'authors', 'authors_ids', 'publisher', 'publisher_name',
            'faculty', 'faculty_name', 'department', 'department_name', 'topic', 'topic_name',
            'genre', 'genre_name', 'description', 'publication_date', 'edition', 'pages',
            'language', 'book_file', 'cover_image', 'qr_code', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'qr_code', 'created_at', 'updated_at']

    def create(self, validated_data):
        authors_ids = validated_data.pop('authors_ids', [])
        book = super().create(validated_data)
        if authors_ids:
            book.authors.set(authors_ids)
        return book

    def update(self, instance, validated_data):
        authors_ids = validated_data.pop('authors_ids', [])
        book = super().update(instance, validated_data)
        if authors_ids:
            book.authors.set(authors_ids)
        return book


class BookCopySerializer(serializers.ModelSerializer):
    """Serializer for BookCopy model."""
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_isbn = serializers.CharField(source='book.isbn', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BookCopy
        fields = [
            'id', 'book', 'book_title', 'book_isbn', 'barcode', 'condition',
            'condition_display', 'status', 'status_display', 'acquisition_date',
            'location', 'qr_code', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'qr_code', 'created_at', 'updated_at']


class BookSearchSerializer(serializers.Serializer):
    """Serializer for book search parameters."""
    q = serializers.CharField(required=False, help_text="Search query")
    author = serializers.CharField(required=False, help_text="Author name")
    title = serializers.CharField(required=False, help_text="Book title")
    isbn = serializers.CharField(required=False, help_text="ISBN number")
    genre = serializers.CharField(required=False, help_text="Genre name")
    publisher = serializers.CharField(required=False, help_text="Publisher name")
    faculty = serializers.CharField(required=False, help_text="Faculty name")
    department = serializers.CharField(required=False, help_text="Department name")
    language = serializers.CharField(required=False, help_text="Language")
    available_only = serializers.BooleanField(default=False, help_text="Show only available books")
