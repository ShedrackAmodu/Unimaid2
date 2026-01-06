from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Document, Collection
from .forms import DocumentForm


def is_staff_user(user):
    return user.groups.filter(name='Staff').exists() or user.is_staff


class DocumentListView(ListView):
    model = Document
    template_name = 'repository/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        queryset = Document.objects.filter(access_level__in=['open', 'restricted'])
        search_query = self.request.GET.get('q')
        collection_filter = self.request.GET.get('collection')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(authors__icontains=search_query) |
                Q(abstract__icontains=search_query)
            )

        if collection_filter:
            queryset = queryset.filter(collection_id=collection_filter)

        return queryset.order_by('-upload_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collections'] = Collection.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_collection'] = self.request.GET.get('collection', '')
        return context


class DocumentDetailView(DetailView):
    model = Document
    template_name = 'repository/document_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        # Only show public documents unless user is staff
        if self.request.user.is_staff or self.request.user.groups.filter(name='Staff').exists():
            return Document.objects.all()
        return Document.objects.filter(access_level='open')


@login_required
@user_passes_test(is_staff_user)
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('repository:document_detail', pk=document.pk)
    else:
        form = DocumentForm()
    return render(request, 'repository/document_form.html', {'form': form, 'action': 'Upload'})


@login_required
@user_passes_test(is_staff_user)
def edit_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'Document updated successfully!')
            return redirect('repository:document_detail', pk=document.pk)
    else:
        form = DocumentForm(instance=document)
    return render(request, 'repository/document_form.html', {'form': form, 'action': 'Edit', 'document': document})


@login_required
@user_passes_test(is_staff_user)
def delete_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        return redirect('repository:document_list')
    return render(request, 'repository/document_confirm_delete.html', {'document': document})


def download_document(request, pk):
    document = get_object_or_404(Document, pk=pk)

    # Check access permissions
    if document.access_level == 'private':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this document.')
            return redirect('accounts:login')
        # Add more complex permission checks here if needed

    # In a real implementation, you'd serve the file properly
    # For now, just redirect to the file URL
    if document.file:
        return redirect(document.file.url)
    else:
        messages.error(request, 'File not found.')
        return redirect('repository:document_detail', pk=pk)


class CollectionListView(ListView):
    model = Collection
    template_name = 'repository/collection_list.html'
    context_object_name = 'collections'
    paginate_by = 20

    def get_queryset(self):
        return Collection.objects.prefetch_related('documents').order_by('name')


class CollectionDetailView(DetailView):
    model = Collection
    template_name = 'repository/collection_detail.html'
    context_object_name = 'collection'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.get_object()
        # Filter documents based on access level
        if self.request.user.is_staff or self.request.user.groups.filter(name='Staff').exists():
            context['documents'] = collection.documents.all()
        else:
            context['documents'] = collection.documents.filter(access_level='open')
        return context
