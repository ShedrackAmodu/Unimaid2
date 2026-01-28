from rest_framework import serializers
from .models import Collection, EBook, EBookPermissionRequest, EBookPermission


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model."""
    curator_name = serializers.CharField(source='curator.get_full_name', read_only=True)
    ebooks_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            'id', 'name', 'description', 'curator', 'curator_name',
            'ebooks_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_ebooks_count(self, obj):
        return obj.ebooks.count()


class EBookSerializer(serializers.ModelSerializer):
    """Serializer for EBook model."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    collection_name = serializers.CharField(source='collection.name', read_only=True)
    access_level_display = serializers.CharField(source='get_access_level_display', read_only=True)
    can_user_access = serializers.SerializerMethodField()

    class Meta:
        model = EBook
        fields = [
            'id', 'title', 'authors', 'abstract', 'file', 'upload_date',
            'access_level', 'access_level_display', 'doi', 'collection',
            'collection_name', 'uploaded_by', 'uploaded_by_name', 'can_user_access',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'upload_date', 'created_at', 'updated_at']

    def get_can_user_access(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_user_access(request.user)
        return False


class EBookPermissionRequestSerializer(serializers.ModelSerializer):
    """Serializer for EBookPermissionRequest model."""
    ebook_title = serializers.CharField(source='ebook.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EBookPermissionRequest
        fields = [
            'id', 'ebook', 'ebook_title', 'user', 'user_name', 'reason',
            'status', 'status_display', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'review_notes', 'requested_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reviewed_by', 'reviewed_at', 'requested_at', 'created_at', 'updated_at']


class EBookPermissionSerializer(serializers.ModelSerializer):
    """Serializer for EBookPermission model."""
    ebook_title = serializers.CharField(source='ebook.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    granted_by_name = serializers.CharField(source='granted_by.get_full_name', read_only=True)

    class Meta:
        model = EBookPermission
        fields = [
            'id', 'ebook', 'ebook_title', 'user', 'user_name', 'granted',
            'granted_by', 'granted_by_name', 'granted_at', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'granted_at', 'created_at', 'updated_at']


class EBookSearchSerializer(serializers.Serializer):
    """Serializer for document search parameters."""
    q = serializers.CharField(required=False, help_text="Search query")
    title = serializers.CharField(required=False, help_text="Document title")
    authors = serializers.CharField(required=False, help_text="Authors")
    collection = serializers.CharField(required=False, help_text="Collection name")
    access_level = serializers.ChoiceField(
        choices=[('open', 'Open Access'), ('restricted', 'Restricted'), ('embargo', 'Embargoed'), ('private', 'Private')],
        required=False,
        help_text="Access level"
    )
    uploaded_by = serializers.CharField(required=False, help_text="Uploader name")
    date_from = serializers.DateField(required=False, help_text="Upload date from")
    date_to = serializers.DateField(required=False, help_text="Upload date to")
