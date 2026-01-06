from django.db import models
from config.models import BaseModel


class Author(BaseModel):
    name = models.CharField(max_length=200, help_text="Full name of the author")
    bio = models.TextField(blank=True, help_text="Biography of the author")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"


class Publisher(BaseModel):
    name = models.CharField(max_length=200, help_text="Name of the publisher")
    address = models.TextField(blank=True, help_text="Address of the publisher")
    website = models.URLField(blank=True, help_text="Website of the publisher")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Publisher"
        verbose_name_plural = "Publishers"


class Faculty(BaseModel):
    name = models.CharField(max_length=200, unique=True, help_text="Name of the faculty")
    description = models.TextField(blank=True, help_text="Description of the faculty")
    code = models.CharField(max_length=10, unique=True, help_text="Faculty code (e.g., SCI, ART)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Faculty"
        verbose_name_plural = "Faculties"


class Department(BaseModel):
    name = models.CharField(max_length=200, help_text="Name of the department")
    description = models.TextField(blank=True, help_text="Description of the department")
    code = models.CharField(max_length=10, unique=True, help_text="Department code")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments', help_text="Faculty this department belongs to")

    def __str__(self):
        return f"{self.name} ({self.faculty.name})"

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        unique_together = ['name', 'faculty']


class Topic(BaseModel):
    name = models.CharField(max_length=200, help_text="Name of the topic")
    description = models.TextField(blank=True, help_text="Description of the topic")
    code = models.CharField(max_length=20, unique=True, help_text="Topic code")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='topics', help_text="Department this topic belongs to")

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        unique_together = ['name', 'department']


class Genre(BaseModel):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the genre")
    description = models.TextField(blank=True, help_text="Description of the genre")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"


class Book(BaseModel):
    title = models.CharField(max_length=500, help_text="Title of the book")
    isbn = models.CharField(max_length=13, unique=True, help_text="ISBN-10 or ISBN-13")
    authors = models.ManyToManyField(Author, related_name='books', help_text="Authors of the book")
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name='books', help_text="Publisher of the book")
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', help_text="Faculty the book belongs to")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', help_text="Department the book belongs to")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', help_text="Academic topic of the book")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', help_text="Genre of the book")
    description = models.TextField(blank=True, help_text="Description of the book")
    publication_date = models.DateField(help_text="Publication date")
    edition = models.CharField(max_length=50, blank=True, help_text="Edition of the book")
    pages = models.PositiveIntegerField(help_text="Number of pages")
    language = models.CharField(max_length=50, default='English', help_text="Language of the book")

    objects = models.Manager()  # Default manager

    class BookManager(models.Manager):
        def active(self):
            # For now, return all books. Later can filter by active status if added
            return self.all()

    objects = BookManager()

    def is_available(self):
        """Check if the book has any available copies."""
        return self.copies.filter(status='available').exists()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"


class BookCopy(BaseModel):
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('checked_out', 'Checked Out'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies', help_text="The book this copy belongs to")
    barcode = models.CharField(max_length=50, unique=True, help_text="Unique barcode for the copy")
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good', help_text="Condition of the copy")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', help_text="Current status of the copy")
    acquisition_date = models.DateField(help_text="Date the copy was acquired")
    location = models.CharField(max_length=100, help_text="Shelf location or storage location")

    class BookCopyManager(models.Manager):
        def available(self):
            return self.filter(status='available')

    objects = BookCopyManager()

    def __str__(self):
        return f"{self.book.title} - Copy {self.barcode}"

    class Meta:
        verbose_name = "Book Copy"
        verbose_name_plural = "Book Copies"
