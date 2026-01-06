from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
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
        return BlogPost.objects.filter(status='published').order_by('-published_date')


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return BlogPost.objects.filter(status='published')


@login_required
@user_passes_test(is_staff_user)
def create_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if post.status == 'published':
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
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Blog post deleted successfully!')
        return redirect('blog:post_list')
    return render(request, 'blog/post_confirm_delete.html', {'post': post})
