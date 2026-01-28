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


class EBook(BaseModel):
    ACCESS_LEVEL_CHOICES = [
        ('open', 'Open Access'),
        ('restricted', 'Restricted'),
        ('embargo', 'Embargoed'),
        ('private', 'Private'),
    ]

    title = models.CharField(max_length=500, help_text="Title of the eBook")
    authors = models.TextField(help_text="Authors of the eBook (comma-separated)")
    abstract = models.TextField(blank=True, help_text="Abstract or summary of the eBook")
    file = models.FileField(upload_to='repository/', help_text="Uploaded file")
    upload_date = models.DateTimeField(auto_now_add=True, help_text="Date the eBook was uploaded")
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='open',
        help_text="Access level for the eBook"
    )
    doi = models.CharField(max_length=100, blank=True, unique=True, help_text="Digital Object Identifier")
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ebooks',
        help_text="Collection this eBook belongs to"
    )
    uploaded_by = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='uploaded_ebooks',
        help_text="User who uploaded the eBook"
    )

    def __str__(self):
        return self.title

    def can_user_access(self, user):
        """Check if a user can access this eBook."""
        if self.access_level == 'open':
            return True

        if not user or not user.is_authenticated:
            return False

        # Admin has access to everything
        if user.is_superuser:
            return True

        # Staff with granted permission can access
        if user.groups.filter(name='Staff').exists():
            return EBookPermission.objects.filter(
                ebook=self,
                user=user,
                granted=True
            ).exists()

        return False

    class Meta:
        verbose_name = "eBook"
        verbose_name_plural = "eBooks"
        ordering = ['-upload_date']


class EBookPermissionRequest(BaseModel):
    """Model for staff members to request access to restricted eBooks."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    ebook = models.ForeignKey(
        EBook,
        on_delete=models.CASCADE,
        related_name='permission_requests',
        help_text="The eBook access is being requested for",
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='ebook_permission_requests',
        help_text="The staff user requesting access",
        limit_choices_to={'groups__name': 'Staff'}
    )
    reason = models.TextField(
        help_text="Reason for requesting access to this eBook"
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
        return f"Request: {self.user.get_full_name()} → {self.ebook.title}"

    def approve(self, admin_user):
        """Approve the permission request and create the permission."""
        from django.utils import timezone

        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

        # Create the actual permission
        EBookPermission.objects.get_or_create(
            ebook=self.ebook,
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
        verbose_name = "eBook Permission Request"
        verbose_name_plural = "eBook Permission Requests"
        unique_together = ('ebook', 'user')
        ordering = ['-requested_at']


class EBookPermission(BaseModel):
    """Model to grant specific eBook access to staff members."""

    ebook = models.ForeignKey(
        EBook,
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="The eBook being granted access to",
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='ebook_permissions',
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
        return f"{status}: {self.user.get_full_name()} → {self.ebook.title}"

    class Meta:
        verbose_name = "eBook Permission"
        verbose_name_plural = "eBook Permissions"
        unique_together = ('ebook', 'user')
        ordering = ['-granted_at']
