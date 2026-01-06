from .models import BlogPost
from django.utils import timezone
from datetime import timedelta

def blog_context(request):
    context = {}

    # Recent published posts for sidebar
    recent_posts = BlogPost.objects.filter(
        status='published',
        published_date__lte=timezone.now()
    ).order_by('-published_date')[:5]

    context['recent_posts'] = recent_posts

    # Archive data (group by month)
    if request.user.is_staff:
        posts_for_archive = BlogPost.objects.all()
    else:
        posts_for_archive = BlogPost.objects.filter(status='published')

    # Get unique months with posts
    archive_months = []
    for post in posts_for_archive:
        if post.published_date:
            month = post.published_date.strftime('%B %Y')
            if month not in [m['month'] for m in archive_months]:
                archive_months.append({
                    'month': month,
                    'date': post.published_date,
                    'count': posts_for_archive.filter(
                        published_date__year=post.published_date.year,
                        published_date__month=post.published_date.month
                    ).count()
                })

    # Sort by date descending
    archive_months.sort(key=lambda x: x['date'], reverse=True)
    context['archive_months'] = archive_months[:6]

    return context
