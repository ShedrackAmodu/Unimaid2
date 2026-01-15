from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Document, Collection, DocumentPermissionRequest
from .forms import DocumentForm


def is_staff_user(user):
    return user.groups.filter(name='Staff').exists() or user.is_staff


class DocumentListView(ListView):
    model = Document
    template_name = 'repository/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        # Only show documents the user can access
        user = self.request.user
        queryset = Document.objects.all()

        # Filter by access permissions
        accessible_docs = []
        for doc in queryset:
            if doc.can_user_access(user):
                accessible_docs.append(doc.pk)

        queryset = queryset.filter(pk__in=accessible_docs)

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
        # Only show documents the user can access
        user = self.request.user
        queryset = Document.objects.all()

        # Filter by access permissions
        accessible_docs = []
        for doc in queryset:
            if doc.can_user_access(user):
                accessible_docs.append(doc.pk)

        return queryset.filter(pk__in=accessible_docs)


@login_required
@user_passes_test(lambda u: u.is_superuser)
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
@user_passes_test(lambda u: u.is_superuser)
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
@user_passes_test(lambda u: u.is_superuser)
def delete_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        return redirect('repository:document_list')
    return render(request, 'repository/document_confirm_delete.html', {'document': document})


def download_document(request, pk):
    document = get_object_or_404(Document, pk=pk)

    # Check access permissions using the new method
    if not document.can_user_access(request.user):
        messages.error(request, 'You do not have permission to access this document.')
        return redirect('repository:document_list')

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
        user = self.request.user

        # Filter documents the user can access
        all_docs = collection.documents.all()
        accessible_docs = []
        for doc in all_docs:
            if doc.can_user_access(user):
                accessible_docs.append(doc)

        context['documents'] = accessible_docs
        return context


@login_required
@user_passes_test(is_staff_user)
def request_document_permission(request, document_id):
    """Allow staff to request access to a restricted document."""
    document = get_object_or_404(Document, pk=document_id)

    # Check if user already has access
    if document.can_user_access(request.user):
        messages.info(request, 'You already have access to this document.')
        return redirect('repository:document_detail', pk=document_id)

    # Check if user already has a pending request
    existing_request = DocumentPermissionRequest.objects.filter(
        document=document,
        user=request.user,
        status='pending'
    ).exists()

    if existing_request:
        messages.warning(request, 'You already have a pending permission request for this document.')
        return redirect('repository:document_detail', pk=document_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Please provide a reason for your request.')
            return redirect('repository:document_detail', pk=document_id)

        # Create permission request
        DocumentPermissionRequest.objects.create(
            document=document,
            user=request.user,
            reason=reason
        )

        messages.success(request, 'Your permission request has been submitted. You will be notified when it is reviewed.')
        return redirect('repository:document_detail', pk=document_id)

    # Show request form
    context = {
        'document': document,
    }
    return render(request, 'repository/request_permission.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def review_permission_requests(request):
    """Admin view to review pending permission requests."""
    pending_requests = DocumentPermissionRequest.objects.filter(
        status='pending'
    ).select_related('document', 'user').order_by('-requested_at')

    context = {
        'pending_requests': pending_requests,
    }
    return render(request, 'repository/review_requests.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_permission_request(request, request_id):
    """Approve a permission request."""
    permission_request = get_object_or_404(
        DocumentPermissionRequest,
        pk=request_id,
        status='pending'
    )

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        permission_request.approve(request.user)

        # Send notification email
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            import logging

            send_mail(
                subject="Document Access Request Approved",
                message=f"Dear {permission_request.user.get_full_name()},\n\n"
                       f"Your request for access to the document '{permission_request.document.title}' has been approved.\n\n"
                       f"You can now access this document in the repository.\n\n"
                       f"Best regards,\nRamat Library Administration",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[permission_request.user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send approval email to {permission_request.user.username}: {e}")
            messages.warning(request, f'Permission approved, but email notification failed. Please inform the user manually.')

        messages.success(request, f'Permission request approved for {permission_request.user.get_full_name()}.')
        return redirect('repository:review_requests')

    return redirect('repository:review_requests')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_permission_request(request, request_id):
    """Reject a permission request."""
    permission_request = get_object_or_404(
        DocumentPermissionRequest,
        pk=request_id,
        status='pending'
    )

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        permission_request.reject(request.user, notes)

        # Send notification email
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            import logging

            send_mail(
                subject="Document Access Request Update",
                message=f"Dear {permission_request.user.get_full_name()},\n\n"
                       f"Your request for access to the document '{permission_request.document.title}' has been rejected.\n\n"
                       f"Reason: {notes}\n\n"
                       f"If you have questions, please contact the library administration.\n\n"
                       f"Best regards,\nRamat Library Administration",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[permission_request.user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send rejection email to {permission_request.user.username}: {e}")
            messages.warning(request, f'Permission rejected, but email notification failed. Please inform the user manually.')

        messages.success(request, f'Permission request rejected for {permission_request.user.get_full_name()}.')
        return redirect('repository:review_requests')

    return redirect('repository:review_requests')


@login_required
@user_passes_test(is_staff_user)
def my_permission_requests(request):
    """Staff view to see their permission requests."""
    requests = DocumentPermissionRequest.objects.filter(
        user=request.user
    ).select_related('document').order_by('-requested_at')

    # Calculate counts
    approved_count = requests.filter(status='approved').count()
    rejected_count = requests.filter(status='rejected').count()

    context = {
        'requests': requests,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'repository/my_requests.html', context)
