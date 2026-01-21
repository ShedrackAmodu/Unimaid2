from rest_framework import serializers
from .models import BlogPost, StaticPage, News, FeaturedContent


class BlogPostSerializer(serializers.ModelSerializer):
    """Serializer for BlogPost model."""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'content', 'author', 'author_name', 'published_date',
            'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaticPageSerializer(serializers.ModelSerializer):
    """Serializer for StaticPage model."""

    class Meta:
        model = StaticPage
        fields = ['id', 'title', 'slug', 'content', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class NewsSerializer(serializers.ModelSerializer):
    """Serializer for News model."""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'author', 'author_name', 'published_date',
            'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FeaturedContentSerializer(serializers.ModelSerializer):
    """Serializer for FeaturedContent model."""

    class Meta:
        model = FeaturedContent
        fields = [
            'id', 'title', 'content', 'image', 'link', 'is_active', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
