from django.contrib import admin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_date']
    list_filter = ['status', 'published_date']
    search_fields = ['title', 'author__username']
