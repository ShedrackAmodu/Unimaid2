from django.contrib import admin
from .models import Collection, Document, DocumentPermission


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'curator']
    search_fields = ['name', 'curator__username']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors', 'access_level', 'upload_date', 'uploaded_by']
    list_filter = ['access_level', 'upload_date']
    search_fields = ['title', 'authors']


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'granted', 'granted_by', 'granted_at']
    list_filter = ['granted', 'granted_at']
    search_fields = ['document__title', 'user__username', 'granted_by__username']
    raw_id_fields = ['document', 'user', 'granted_by']
