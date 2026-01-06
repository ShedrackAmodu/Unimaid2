from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone


class BaseAdminMixin:
    """Base admin mixin with common functionality."""

    list_per_page = 25
    save_on_top = True
    view_on_site = True

    def get_list_display(self, request):
        """Add action buttons to list display."""
        base_list = super().get_list_display(request)
        if not base_list:
            base_list = []
        return list(base_list) + ['_actions']

    def _actions(self, obj):
        """Display action buttons."""
        change_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=[obj.id]
        )
        delete_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete',
            args=[obj.id]
        )
        history_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_history',
            args=[obj.id]
        )

        return format_html(
            '<div class="action-buttons">'
            '<a href="{}" class="btn btn-sm btn-outline-primary" title="Edit">'
            '<i class="bi bi-pencil"></i></a> '
            '<a href="{}" class="btn btn-sm btn-outline-danger" title="Delete">'
            '<i class="bi bi-trash"></i></a> '
            '<a href="{}" class="btn btn-sm btn-outline-info" title="History">'
            '<i class="bi bi-clock-history"></i></a>'
            '</div>',
            change_url, delete_url, history_url
        )
    _actions.short_description = 'Actions'
    _actions.allow_tags = True


class ExportMixin:
    """Mixin for export functionality."""

    def export_as_csv(self, request, queryset):
        """Export selected items as CSV."""
        import csv
        from django.http import HttpResponse
        import io

        field_names = [field.name for field in self.model._meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={self.model._meta.verbose_name_plural}.csv'

        writer = csv.writer(response)
        writer.writerow(field_names)

        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export selected items as CSV"


class ChartMixin:
    """Mixin for chart display."""

    change_list_template = "admin/charts_change_list.html"

    def changelist_view(self, request, extra_context=None):
        """Add chart data to changelist view."""
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data'):
            # Add chart data
            chart_data = self.get_chart_data(request)
            if chart_data:
                response.context_data['chart_data'] = chart_data

        return response

    def get_chart_data(self, request):
        """Override this method to provide chart data."""
        return None


class StatusFilterMixin:
    """Mixin for status filtering."""

    def get_queryset(self, request):
        """Filter queryset based on status."""
        qs = super().get_queryset(request)

        status_filter = request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_list_filter(self, request):
        """Add status filter to list filter."""
        base_filters = super().get_list_filter(request)
        if not base_filters:
            base_filters = []
        return list(base_filters) + ['status']
