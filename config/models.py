from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model providing timestamp fields for all models.
    All models in the library system should inherit from this base.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the record was last updated")

    class Meta:
        abstract = True
