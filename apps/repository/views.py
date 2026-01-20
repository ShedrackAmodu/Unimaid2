from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q
from .models import EBook, Collection, EBookPermissionRequest
from .forms import EBookForm


def is_staff_user(user):
    return user.groups.filter(name='Staff').exists() or user.is_staff


class EBookListView(ListView):
    model = EBook
    template_name = 'repository/ebook_list.html'
    context_object_name = 'ebooks'
    paginate_by = 20

    def get_queryset(self):
        # Only show ebooks the user can access
        user = self.request.user
        queryset = EBook.objects.all()

        # Filter by access permissions
        accessible_ebooks = []
        for ebook in queryset:
            if ebook.can_user_access(user):
                accessible_ebooks.append(ebook.pk)

        queryset = queryset.filter(pk__in=accessible_ebooks)

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


class EBookDetailView(DetailView):
    model = EBook
    template_name = 'repository/ebook_detail.html'
    context_object_name = 'ebook'

    def get_queryset(self):
        # Only show ebooks the user can access
        user = self.request.user
        queryset = EBook.objects.all()

        # Filter by access permissions
        accessible_ebooks = []
        for ebook in queryset:
            if ebook.can_user_access(user):
                accessible_ebooks.append(ebook.pk)

        return queryset.filter(pk__in=accessible_ebooks)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def upload_ebook(request):
    if request.method == 'POST':
        form = EBookForm(request.POST, request.FILES)
        if form.is_valid():
            ebook = form.save(commit=False)
            ebook.uploaded_by = request.user
            ebook.save()
            messages.success(request, 'eBook uploaded successfully!')
            return redirect('repository:ebook_detail', pk=ebook.pk)
    else:
        form = EBookForm()
    return render(request, 'repository/ebook_form.html', {'form': form, 'action': 'Upload'})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_ebook(request, pk):
    ebook = get_object_or_404(EBook, pk=pk)
    if request.method == 'POST':
        form = EBookForm(request.POST, request.FILES, instance=ebook)
        if form.is_valid():
            form.save()
            messages.success(request, 'eBook updated successfully!')
            return redirect('repository:ebook_detail', pk=ebook.pk)
    else:
        form = EBookForm(instance=ebook)
    return render(request, 'repository/ebook_form.html', {'form': form, 'action': 'Edit', 'ebook': ebook})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_ebook(request, pk):
    ebook = get_object_or_404(EBook, pk=pk)
    if request.method == 'POST':
        ebook.delete()
        messages.success(request, 'eBook deleted successfully!')
        return redirect('repository:ebook_list')
    return render(request, 'repository/ebook_confirm_delete.html', {'ebook': ebook})


def download_ebook(request, pk):
    ebook = get_object_or_404(EBook, pk=pk)

    # Check access permissions using the new method
    if not ebook.can_user_access(request.user):
        messages.error(request, 'You do not have permission to access this eBook.')
        return redirect('repository:ebook_list')

    # In a real implementation, you'd serve the file properly
    # For now, just redirect to the file URL
    if ebook.file:
        return redirect(ebook.file.url)
    else:
        messages.error(request, 'File not found.')
        return redirect('repository:ebook_detail', pk=pk)


class CollectionListView(ListView):
    model = Collection
    template_name = 'repository/collection_list.html'
    context_object_name = 'collections'
    paginate_by = 20

    def get_queryset(self):
        return Collection.objects.prefetch_related('ebooks').order_by('name')


class CollectionDetailView(DetailView):
    model = Collection
    template_name = 'repository/collection_detail.html'
    context_object_name = 'collection'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.get_object()
        user = self.request.user

        # Filter ebooks the user can access
        all_ebooks = collection.ebooks.all()
        accessible_ebooks = []
        for ebook in all_ebooks:
            if ebook.can_user_access(user):
                accessible_ebooks.append(ebook)

        context['ebooks'] = accessible_ebooks
        return context


@login_required
@user_passes_test(is_staff_user)
def request_ebook_permission(request, ebook_id):
    """Allow staff to request access to a restricted eBook."""
    ebook = get_object_or_404(EBook, pk=ebook_id)

    # Check if user already has access
    if ebook.can_user_access(request.user):
        messages.info(request, 'You already have access to this eBook.')
        return redirect('repository:ebook_detail', pk=ebook_id)

    # Check if user already has a pending request
    existing_request = EBookPermissionRequest.objects.filter(
        ebook=ebook,
        user=request.user,
        status='pending'
    ).exists()

    if existing_request:
        messages.warning(request, 'You already have a pending permission request for this eBook.')
        return redirect('repository:ebook_detail', pk=ebook_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Please provide a reason for your request.')
            return redirect('repository:ebook_detail', pk=ebook_id)

        # Create permission request
        EBookPermissionRequest.objects.create(
            ebook=ebook,
            user=request.user,
            reason=reason
        )

        messages.success(request, 'Your permission request has been submitted. You will be notified when it is reviewed.')
        return redirect('repository:ebook_detail', pk=ebook_id)

    # Show request form
    context = {
        'ebook': ebook,
    }
    return render(request, 'repository/request_permission.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def review_permission_requests(request):
    """Admin view to review pending permission requests."""
    pending_requests = EBookPermissionRequest.objects.filter(
        status='pending'
    ).select_related('ebook', 'user').order_by('-requested_at')

    context = {
        'pending_requests': pending_requests,
    }
    return render(request, 'repository/review_requests.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_permission_request(request, request_id):
    """Approve a permission request."""
    permission_request = get_object_or_404(
        EBookPermissionRequest,
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
                subject="eBook Access Request Approved",
                message=f"Dear {permission_request.user.get_full_name()},\n\n"
                       f"Your request for access to the eBook '{permission_request.ebook.title}' has been approved.\n\n"
                       f"You can now access this eBook in the repository.\n\n"
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
        EBookPermissionRequest,
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
                subject="eBook Access Request Update",
                message=f"Dear {permission_request.user.get_full_name()},\n\n"
                       f"Your request for access to the eBook '{permission_request.ebook.title}' has been rejected.\n\n"
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
    requests = EBookPermissionRequest.objects.filter(
        user=request.user
    ).select_related('ebook').order_by('-requested_at')

    # Calculate counts
    approved_count = requests.filter(status='approved').count()
    rejected_count = requests.filter(status='rejected').count()

    context = {
        'requests': requests,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'repository/my_requests.html', context)
