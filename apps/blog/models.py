from django.db import models
from config.models import BaseModel
from apps.accounts.models import LibraryUser


class BlogPost(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=500, help_text="Title of the blog post")
    content = models.TextField(help_text="Content of the blog post")
    author = models.ForeignKey(
        LibraryUser,
        on_delete=models.CASCADE,
        related_name='blog_posts',
        help_text="Author of the blog post"
    )
    published_date = models.DateTimeField(null=True, blank=True, help_text="Date the post was published")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Publication status of the post"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-published_date', '-created_at']
