from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from .models import BlogPost
from .forms import BlogPostForm


def is_staff_user(user):
    return user.groups.filter(name='Staff').exists() or user.is_staff


class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        # Non-staff users only see published posts
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset.order_by('-published_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add staff check to context
        context['user_is_staff'] = self.request.user.is_staff

        # Add archive entries (published posts grouped by month)
        archive_entries = BlogPost.objects.filter(
            status='published',
            published_date__isnull=False
        ).annotate(
            month=TruncMonth('published_date')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('-month')[:12]  # Last 12 months

        context['archive_entries'] = archive_entries
        return context


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        if self.request.user.is_staff:
            return BlogPost.objects.all()
        return BlogPost.objects.filter(status='published')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()

        # Get related posts (same author or similar titles)
        related_posts = BlogPost.objects.filter(
            Q(author=post.author) | Q(title__icontains=post.title.split()[0])
        ).exclude(pk=post.pk).filter(status='published')[:3]

        # Get next and previous posts
        if self.request.user.is_staff:
            all_posts = BlogPost.objects.all().order_by('-published_date', '-created_at')
        else:
            all_posts = BlogPost.objects.filter(status='published').order_by('-published_date', '-created_at')

        post_list = list(all_posts)
        current_index = post_list.index(post) if post in post_list else -1

        if current_index > 0:
            context['previous_post'] = post_list[current_index - 1]
        if current_index < len(post_list) - 1:
            context['next_post'] = post_list[current_index + 1]

        context['related_posts'] = related_posts
        context['user_is_staff'] = self.request.user.is_staff
        return context


@login_required
@user_passes_test(is_staff_user)
def create_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if post.status == 'published' and not post.published_date:
                post.published_date = timezone.now()
            post.save()
            messages.success(request, 'Blog post created successfully!')
            return redirect('blog:post_detail', pk=post.pk)
    else:
        form = BlogPostForm()
    return render(request, 'blog/post_form.html', {'form': form, 'action': 'Create'})


@login_required
@user_passes_test(is_staff_user)
def edit_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    # Only allow authors or staff to edit
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('blog:post_detail', pk=pk)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            if post.status == 'published' and not post.published_date:
                post.published_date = timezone.now()
            post.save()
            messages.success(request, 'Blog post updated successfully!')
            return redirect('blog:post_detail', pk=post.pk)
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'blog/post_form.html', {'form': form, 'action': 'Edit', 'post': post})


@login_required
@user_passes_test(is_staff_user)
def delete_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    # Only allow authors or staff to delete
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only delete your own posts.')
        return redirect('blog:post_detail', pk=pk)

    if request.method == 'POST':
        post_title = post.title
        post.delete()
        messages.success(request, f'Blog post "{post_title}" deleted successfully!')
        return redirect('blog:post_list')
    return render(request, 'blog/post_confirm_delete.html', {'post': post})


# Additional view for publishing drafts
@login_required
@user_passes_test(is_staff_user)
def publish_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only publish your own posts.')
        return redirect('blog:post_detail', pk=pk)

    if post.status == 'draft':
        post.status = 'published'
        if not post.published_date:
            post.published_date = timezone.now()
        post.save()
        messages.success(request, 'Blog post published successfully!')

    return redirect('blog:post_detail', pk=pk)


# View for staff to see all drafts
@login_required
@user_passes_test(is_staff_user)
def draft_posts(request):
    drafts = BlogPost.objects.filter(status='draft', author=request.user)
    return render(request, 'blog/draft_list.html', {'drafts': drafts})
