from django.contrib import admin
from .models import Collection, Document


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'curator']
    search_fields = ['name', 'curator__username']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors', 'access_level', 'upload_date', 'uploaded_by']
    list_filter = ['access_level', 'upload_date']
    search_fields = ['title', 'authors']
