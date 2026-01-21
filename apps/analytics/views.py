from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
import json
from .models import AnalyticsEvent, DailyStats, PopularItem, SystemHealth
from .forms import AnalyticsSettingsForm, ReportGenerationForm, DateRangeForm


class AnalyticsDashboardView(TemplateView):
    """Main analytics dashboard view for administrators and staff."""
    template_name = 'analytics/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        # Only allow superusers and staff with analytics access
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if not (request.user.is_superuser or request.user.is_staff):
            return HttpResponseForbidden("Access denied. Analytics dashboard requires administrative privileges.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get date range from URL parameters or default to 30 days
        days = int(self.request.GET.get('days', 30))
        context['days'] = days

        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Get daily stats for the period
        daily_stats = DailyStats.objects.filter(date__gte=start_date, date__lte=end_date).order_by('date')
        context['daily_stats'] = daily_stats

        # Calculate summary statistics
        context.update(self._get_summary_stats(start_date, end_date))

        # Get popular items
        context['popular_books'] = PopularItem.objects.filter(item_type='book').order_by('-total_score')[:10]
        context['popular_documents'] = PopularItem.objects.filter(item_type='document').order_by('-total_score')[:10]

        # Get recent events
        context['recent_events'] = AnalyticsEvent.objects.select_related(
            'user', 'book', 'document'
        ).order_by('-created_at')[:20]

        # Get system health
        context['system_health'] = SystemHealth.objects.first()

        # Get user activity data for charts
        context['chart_data'] = self._get_chart_data(start_date, end_date)

        return context

    def _get_summary_stats(self, start_date, end_date):
        """Calculate summary statistics for the dashboard."""
        # Total users
        from apps.accounts.models import LibraryUser
        total_users = LibraryUser.objects.count()

        # Active users (logged in within the period)
        active_users = LibraryUser.objects.filter(
            last_login__date__gte=start_date
        ).count()

        # New users in period
        new_users = LibraryUser.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).count()

        # Book statistics
        from apps.catalog.models import Book, BookCopy
        total_books = Book.objects.active().count()
        available_books = BookCopy.objects.filter(status='available').count()
        checked_out_books = BookCopy.objects.filter(status='checked_out').count()

        # Circulation statistics
        from apps.circulation.models import Loan
        total_loans = Loan.objects.count()
        active_loans = Loan.objects.filter(status='active').count()
        overdue_loans = Loan.objects.filter(
            status='active',
            due_date__date__lt=timezone.now().date()
        ).count()

        # Repository statistics
        from apps.repository.models import Document
        total_documents = Document.objects.count()
        document_downloads = AnalyticsEvent.objects.filter(
            event_type='download',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()

        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users': new_users,
            'total_books': total_books,
            'available_books': available_books,
            'checked_out_books': checked_out_books,
            'total_loans': total_loans,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'total_documents': total_documents,
            'document_downloads': document_downloads,
        }

    def _get_chart_data(self, start_date, end_date):
        """Prepare data for charts."""
        # Daily activity data
        daily_data = []
        current_date = start_date

        while current_date <= end_date:
            day_stats = DailyStats.objects.filter(date=current_date).first()

            if day_stats:
                daily_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'loans': day_stats.total_loans,
                    'returns': day_stats.returned_today,
                    'page_views': day_stats.page_views,
                    'searches': day_stats.searches,
                    'logins': day_stats.logins,
                })
            else:
                daily_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'loans': 0,
                    'returns': 0,
                    'page_views': 0,
                    'searches': 0,
                    'logins': 0,
                })

            current_date += timedelta(days=1)

        # Event type distribution
        event_types = AnalyticsEvent.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('event_type').annotate(count=Count('event_type')).order_by('-count')

        event_distribution = []
        for event in event_types:
            event_distribution.append({
                'type': event['event_type'].replace('_', ' ').title(),
                'count': event['count']
            })

        return {
            'daily_activity': daily_data,
            'event_distribution': event_distribution,
        }


@login_required
@user_passes_test(lambda u: u.is_superuser)
def analytics_reports_view(request):
    """Detailed analytics reports view."""
    # Get form data
    report_form = ReportGenerationForm(request.POST or None)
    date_form = DateRangeForm(request.POST or None)

    if request.method == 'POST' and report_form.is_valid() and date_form.is_valid():
        report_type = report_form.cleaned_data['report_type']
        start_date = date_form.cleaned_data['start_date']
        end_date = date_form.cleaned_data['end_date']
        format_type = report_form.cleaned_data['format']

        # Generate report data based on type
        report_data = generate_report_data(report_type, start_date, end_date)

        if format_type == 'html':
            return render(request, 'analytics/report_detail.html', {
                'report_data': report_data,
                'report_type': report_type,
                'start_date': start_date,
                'end_date': end_date,
            })
        elif format_type == 'json':
            return JsonResponse(report_data)
        else:
            # For PDF/Excel, we'd implement proper export
            messages.info(request, f'Report generation for {format_type} format is not yet implemented.')
            return redirect('analytics:reports')

    context = {
        'report_form': report_form,
        'date_form': date_form,
    }

    return render(request, 'analytics/reports.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def system_health_view(request):
    """System health monitoring view."""
    # Get recent health checks
    health_checks = SystemHealth.objects.order_by('-checked_at')[:50]

    # Get current health status
    latest_health = SystemHealth.objects.first()

    # Calculate health metrics
    avg_response_time = health_checks.aggregate(avg_time=Avg('response_time'))['avg_time']
    error_rate = health_checks.filter(error_count__gt=0).count() / max(health_checks.count(), 1) * 100

    context = {
        'health_checks': health_checks,
        'latest_health': latest_health,
        'avg_response_time': avg_response_time,
        'error_rate': error_rate,
    }

    return render(request, 'analytics/system_health.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def event_analytics_view(request):
    """Event tracking analytics view."""
    # Get event filters
    event_type = request.GET.get('event_type', '')
    user_id = request.GET.get('user', '')
    days = int(request.GET.get('days', 30))

    # Base queryset
    events = AnalyticsEvent.objects.select_related('user', 'book', 'document')

    # Apply filters
    if event_type:
        events = events.filter(event_type=event_type)

    if user_id:
        events = events.filter(user_id=user_id)

    # Date filter
    start_date = timezone.now() - timedelta(days=days)
    events = events.filter(created_at__gte=start_date)

    # Paginate results
    paginator = Paginator(events.order_by('-created_at'), 50)
    page_number = request.GET.get('page')
    events_page = paginator.get_page(page_number)

    # Get event type choices for filter
    event_choices = AnalyticsEvent.EVENT_TYPES

    # Get active users for filter
    from apps.accounts.models import LibraryUser
    active_users = LibraryUser.objects.filter(
        last_login__date__gte=timezone.now().date() - timedelta(days=90)
    ).order_by('last_name', 'first_name')

    context = {
        'events': events_page,
        'event_choices': event_choices,
        'active_users': active_users,
        'selected_event_type': event_type,
        'selected_user': user_id,
        'days': days,
    }

    return render(request, 'analytics/event_analytics.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def analytics_settings_view(request):
    """Analytics settings and configuration."""
    if request.method == 'POST':
        form = AnalyticsSettingsForm(request.POST)
        if form.is_valid():
            # Save settings (implement based on your settings model)
            messages.success(request, 'Analytics settings updated successfully.')
            return redirect('analytics:settings')
    else:
        form = AnalyticsSettingsForm()

    context = {
        'form': form,
    }

    return render(request, 'analytics/settings.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_analytics_data(request):
    """Export analytics data in various formats."""
    format_type = request.GET.get('format', 'csv')
    data_type = request.GET.get('type', 'events')
    days = int(request.GET.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)

    if data_type == 'events':
        queryset = AnalyticsEvent.objects.filter(created_at__gte=start_date)
        filename = f'analytics_events_{timezone.now().date()}'
    elif data_type == 'daily_stats':
        queryset = DailyStats.objects.filter(date__gte=start_date)
        filename = f'daily_stats_{timezone.now().date()}'
    elif data_type == 'popular_items':
        queryset = PopularItem.objects.all()
        filename = f'popular_items_{timezone.now().date()}'
    else:
        return HttpResponse("Invalid data type", status=400)

    # For now, return JSON - in production you'd implement proper CSV/Excel export
    data = []
    for item in queryset[:1000]:  # Limit for performance
        data.append(item.__dict__)

    response = JsonResponse(data, safe=False)
    response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
    return response


def generate_report_data(report_type, start_date, end_date):
    """Generate report data based on report type."""
    if report_type == 'user_activity':
        # User activity report
        from apps.accounts.models import LibraryUser

        users = LibraryUser.objects.annotate(
            loan_count=Count('loans'),
            login_count=Count('analytics_events', filter=Q(analytics_events__event_type='login'))
        ).filter(
            Q(loans__created_at__date__gte=start_date, loans__created_at__date__lte=end_date) |
            Q(analytics_events__created_at__date__gte=start_date, analytics_events__created_at__date__lte=end_date)
        ).distinct()

        return {
            'title': 'User Activity Report',
            'period': f'{start_date} to {end_date}',
            'users': [
                {
                    'name': user.get_full_name(),
                    'email': user.email,
                    'loans': user.loan_count,
                    'logins': user.login_count,
                    'membership_type': user.membership_type,
                } for user in users
            ]
        }

    elif report_type == 'circulation_summary':
        # Circulation summary report
        from apps.circulation.models import Loan

        loans = Loan.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        return {
            'title': 'Circulation Summary Report',
            'period': f'{start_date} to {end_date}',
            'total_loans': loans.count(),
            'active_loans': loans.filter(status='active').count(),
            'overdue_loans': loans.filter(status='active', due_date__date__lt=timezone.now().date()).count(),
            'returned_loans': loans.filter(status='returned').count(),
        }

    elif report_type == 'popular_items':
        # Popular items report
        popular_books = PopularItem.objects.filter(item_type='book').order_by('-total_score')[:20]
        popular_docs = PopularItem.objects.filter(item_type='document').order_by('-total_score')[:20]

        return {
            'title': 'Popular Items Report',
            'period': f'{start_date} to {end_date}',
            'popular_books': [
                {
                    'title': item.book.title if item.book else 'Unknown',
                    'score': item.total_score,
                    'views': item.view_count,
                    'checkouts': item.checkout_count,
                } for item in popular_books
            ],
            'popular_documents': [
                {
                    'title': item.document.title if item.document else 'Unknown',
                    'score': item.total_score,
                    'views': item.view_count,
                    'downloads': item.checkout_count,
                } for item in popular_docs
            ]
        }

    return {'error': 'Unknown report type'}
