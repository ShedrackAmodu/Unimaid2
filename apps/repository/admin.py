from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.text import slugify
import os
import uuid
from .models import Collection, EBook, EBookPermission
from .forms import BulkUploadForm
from config.bulk_actions import bulk_update_ebook_access_level


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'curator']
    search_fields = ['name', 'curator__username']


@admin.register(EBook)
class EBookAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors', 'access_level', 'upload_date', 'uploaded_by']
    list_filter = ['access_level', 'upload_date']
    search_fields = ['title', 'authors']
    actions = ['bulk_upload_ebooks', bulk_update_ebook_access_level]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_file_upload_view), name='repository_ebook_bulk_upload'),
        ]
        return custom_urls + urls

    def bulk_file_upload_view(self, request):
        """Custom view for bulk uploading eBook files locally."""
        # Ensure user is admin
        if not request.user.is_superuser:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('admin:index')

        if request.method == 'POST':
            form = BulkUploadForm(request.POST, request.FILES)

            if form.is_valid():
                uploaded_files = request.FILES.getlist('files')
                access_level = form.cleaned_data['access_level']
                collection = form.cleaned_data.get('collection')

                if not uploaded_files:
                    messages.error(request, 'Please select at least one file to upload.')
                    return redirect('admin:repository_ebook_bulk_upload')

                # Check for maximum limit (50 files)
                if len(uploaded_files) > 50:
                    messages.error(request, 'Maximum 50 files allowed per batch. Please reduce the number of files.')
                    return redirect('admin:repository_ebook_bulk_upload')

                uploaded_count = 0
                errors = []

                # Valid file extensions
                valid_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx']

                for uploaded_file in uploaded_files:
                    try:
                        # Validate file size (max 50MB)
                        if uploaded_file.size > 50 * 1024 * 1024:  # 50MB
                            errors.append(f'File too large ({uploaded_file.size / (1024 * 1024):.1f}MB): {uploaded_file.name} (max 50MB)')
                            continue

                        # Validate file extension
                        file_name, file_ext = os.path.splitext(uploaded_file.name.lower())
                        if file_ext not in valid_extensions:
                            errors.append(f'Unsupported file type "{file_ext}": {uploaded_file.name}. Supported: {", ".join(valid_extensions)}')
                            continue

                        # Ensure unique filename
                        unique_filename = f'{slugify(file_name)}_{uuid.uuid4().hex[:8]}{file_ext}'

                        # Extract title from filename
                        title = file_name.replace('_', ' ').replace('-', ' ').title()
                        if not title:
                            title = f'eBook {uploaded_count + 1}'

                        # Create ebook record
                        ebook = EBook.objects.create(
                            title=title,
                            authors='Unknown',  # Will be updated later
                            file=uploaded_file,
                            access_level=access_level,
                            collection=collection,
                            uploaded_by=request.user
                        )

                        # Rename the file to unique name
                        ebook.file.name = unique_filename
                        ebook.save()

                        uploaded_count += 1

                    except Exception as e:
                        errors.append(f'Failed to process {uploaded_file.name}: {str(e)}')

                # Report results
                if uploaded_count > 0:
                    messages.success(request, f'Successfully uploaded {uploaded_count} eBooks.')

                if errors:
                    for error in errors:
                        messages.error(request, error)

                return redirect('admin:repository_ebook_changelist')
            else:
                # Form validation errors
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        messages.error(request, f'{field}: {error}')

        else:
            form = BulkUploadForm()

        # GET request - show form
        context = {
            'title': 'Bulk Upload eBooks',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'form': form,
        }

        return render(request, 'admin/repository/ebook/bulk_upload.html', context)

    def bulk_upload_ebooks(self, request, queryset):
        """Admin action to redirect to bulk upload page."""
        return HttpResponseRedirect(reverse('admin:repository_ebook_bulk_upload'))
    bulk_upload_ebooks.short_description = 'Bulk upload eBooks'


@admin.register(EBookPermission)
class EBookPermissionAdmin(admin.ModelAdmin):
    list_display = ['ebook', 'user', 'granted', 'granted_by', 'granted_at']
    list_filter = ['granted', 'granted_at']
    search_fields = ['ebook__title', 'user__username', 'granted_by__username']
    raw_id_fields = ['ebook', 'user', 'granted_by']
