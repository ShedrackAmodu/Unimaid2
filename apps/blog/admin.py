from django.contrib import admin
from .models import BlogPost, StaticPage, FeaturedContent, News
from config.bulk_actions import (
    bulk_update_blog_status, bulk_update_news_status,
    bulk_update_static_page_status, bulk_update_featured_content_order
)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_date']
    list_filter = ['status', 'published_date']
    search_fields = ['title', 'author__username']
    actions = [bulk_update_blog_status]


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    actions = [bulk_update_static_page_status]


@admin.register(FeaturedContent)
class FeaturedContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['title']
    list_editable = ['order']
    actions = [bulk_update_featured_content_order]


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_date']
    list_filter = ['status', 'published_date']
    search_fields = ['title', 'author__username']
    actions = [bulk_update_news_status]
