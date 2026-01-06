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


class StaticPage(BaseModel):
    title = models.CharField(max_length=500, help_text="Title of the static page")
    slug = models.SlugField(unique=True, help_text="URL slug for the page")
    content = models.TextField(help_text="Content of the static page")
    is_active = models.BooleanField(default=True, help_text="Whether the page is active")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Static Page"
        verbose_name_plural = "Static Pages"


class FeaturedContent(BaseModel):
    title = models.CharField(max_length=500, help_text="Title of the featured content")
    content = models.TextField(blank=True, help_text="Short description")
    image = models.ImageField(upload_to='featured/', blank=True, null=True, help_text="Featured image")
    link = models.URLField(blank=True, help_text="Link URL")
    is_active = models.BooleanField(default=True, help_text="Whether the content is active")
    order = models.PositiveIntegerField(default=0, help_text="Display order")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Featured Content"
        verbose_name_plural = "Featured Content"
        ordering = ['order', '-created_at']
