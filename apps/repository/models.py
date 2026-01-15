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

    def can_user_access(self, user):
        """Check if a user can access this document."""
        if self.access_level == 'open':
            return True

        if not user or not user.is_authenticated:
            return False

        # Admin has access to everything
        if user.is_superuser:
            return True

        # Staff with granted permission can access
        if user.groups.filter(name='Staff').exists():
            return DocumentPermission.objects.filter(
                document=self,
                user=user,
                granted=True
            ).exists()

        return False

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-upload_date']


class DocumentPermissionRequest(BaseModel):
    """Model for staff members to request access to restricted documents."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='permission_requests',
        help_text="The document access is being requested for"
    )
    user = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='document_permission_requests',
        help_text="The staff user requesting access",
        limit_choices_to={'groups__name': 'Staff'}
    )
    reason = models.TextField(
        help_text="Reason for requesting access to this document"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of the permission request"
    )
    reviewed_by = models.ForeignKey(
        LibraryUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_permission_requests',
        help_text="Admin who reviewed this request"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was reviewed"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Notes from the admin review"
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the request was made"
    )

    def __str__(self):
        return f"Request: {self.user.get_full_name()} → {self.document.title}"

    def approve(self, admin_user):
        """Approve the permission request and create the permission."""
        from django.utils import timezone

        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

        # Create the actual permission
        DocumentPermission.objects.get_or_create(
            document=self.document,
            user=self.user,
            defaults={
                'granted': True,
                'granted_by': admin_user,
                'notes': f"Approved request: {self.reason}"
            }
        )

    def reject(self, admin_user, notes=''):
        """Reject the permission request."""
        from django.utils import timezone

        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    class Meta:
        verbose_name = "Document Permission Request"
        verbose_name_plural = "Document Permission Requests"
        unique_together = ('document', 'user')
        ordering = ['-requested_at']


class DocumentPermission(BaseModel):
    """Model to grant specific document access to staff members."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="The document being granted access to"
    )
    user = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='document_permissions',
        help_text="The staff user being granted access",
        limit_choices_to={'groups__name': 'Staff'}
    )
    granted = models.BooleanField(
        default=True,
        help_text="Whether access is granted or revoked"
    )
    granted_by = models.ForeignKey(
        LibraryUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_permissions',
        help_text="Admin who granted this permission"
    )
    granted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the permission was granted"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about why access was granted"
    )

    def __str__(self):
        status = "Granted" if self.granted else "Revoked"
        return f"{status}: {self.user.get_full_name()} → {self.document.title}"

    class Meta:
        verbose_name = "Document Permission"
        verbose_name_plural = "Document Permissions"
        unique_together = ('document', 'user')
        ordering = ['-granted_at']
