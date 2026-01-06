from django.db import models
from config.models import BaseModel
from apps.accounts.models import LibraryUser


class Collection(BaseModel):
    name = models.CharField(max_length=200, help_text="Name of the collection")
    description = models.TextField(blank=True, help_text="Description of the collection")
    curator = models.ForeignKey(
        LibraryUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curated_collections',
        help_text="User responsible for curating this collection"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"


class Document(BaseModel):
    ACCESS_LEVEL_CHOICES = [
        ('open', 'Open Access'),
        ('restricted', 'Restricted'),
        ('embargo', 'Embargoed'),
        ('private', 'Private'),
    ]

    title = models.CharField(max_length=500, help_text="Title of the document")
    authors = models.TextField(help_text="Authors of the document (comma-separated)")
    abstract = models.TextField(blank=True, help_text="Abstract or summary of the document")
    file = models.FileField(upload_to='repository/', help_text="Uploaded file")
    upload_date = models.DateTimeField(auto_now_add=True, help_text="Date the document was uploaded")
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='open',
        help_text="Access level for the document"
    )
    doi = models.CharField(max_length=100, blank=True, unique=True, help_text="Digital Object Identifier")
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Collection this document belongs to"
    )
    uploaded_by = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        help_text="User who uploaded the document"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-upload_date']
