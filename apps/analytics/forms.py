from django import forms
from django.utils import timezone
from datetime import timedelta


class DateRangeForm(forms.Form):
    """Form for selecting date ranges in analytics."""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Start Date"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="End Date"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values to last 30 days
        if not self.is_bound:
            today = timezone.now().date()
            self.fields['end_date'].initial = today
            self.fields['start_date'].initial = today - timedelta(days=30)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date cannot be after end date.")
            if (end_date - start_date).days > 365:
                raise forms.ValidationError("Date range cannot exceed 365 days.")

        return cleaned_data


class ReportGenerationForm(forms.Form):
    """Form for generating analytics reports."""
    REPORT_TYPES = [
        ('user_activity', 'User Activity Report'),
        ('circulation_summary', 'Circulation Summary'),
        ('popular_items', 'Popular Items Report'),
        ('system_usage', 'System Usage Report'),
        ('event_summary', 'Event Summary'),
    ]

    FORMAT_TYPES = [
        ('html', 'HTML (View in Browser)'),
        ('json', 'JSON (API Format)'),
        ('csv', 'CSV (Spreadsheet)'),
        ('pdf', 'PDF (Printable)'),
        ('excel', 'Excel (Advanced Analysis)'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Report Type"
    )

    format = forms.ChoiceField(
        choices=FORMAT_TYPES,
        initial='html',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Export Format"
    )

    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Include Charts and Visualizations"
    )

    include_raw_data = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Include Raw Data Tables"
    )

    email_report = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Email Report When Generated"
    )

    email_recipients = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@example.com, manager@example.com'
        }),
        label="Email Recipients",
        help_text="Comma-separated email addresses"
    )

    def clean(self):
        cleaned_data = super().clean()
        email_report = cleaned_data.get('email_report')
        email_recipients = cleaned_data.get('email_recipients')

        if email_report and not email_recipients:
            raise forms.ValidationError("Email recipients are required when emailing reports.")

        return cleaned_data


class AnalyticsSettingsForm(forms.Form):
    """Form for configuring analytics settings."""
    enable_tracking = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Enable User Activity Tracking",
        help_text="Track user actions like page views, searches, and logins"
    )

    enable_popular_items = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Track Popular Items",
        help_text="Calculate and display most popular books and documents"
    )

    enable_system_health = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Monitor System Health",
        help_text="Track system performance and error rates"
    )

    retention_days = forms.IntegerField(
        min_value=30,
        max_value=3650,
        initial=365,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '30',
            'max': '3650'
        }),
        label="Data Retention (Days)",
        help_text="How long to keep analytics data (30-3650 days)"
    )

    daily_stats_update = forms.ChoiceField(
        choices=[
            ('manual', 'Manual Updates Only'),
            ('daily', 'Daily (Midnight)'),
            ('hourly', 'Hourly Updates'),
        ],
        initial='daily',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Daily Statistics Update Frequency"
    )

    alert_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Alert Email Address",
        help_text="Email address for system alerts and notifications"
    )

    enable_error_alerts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Enable Error Alerts",
        help_text="Send alerts when system errors occur"
    )

    enable_performance_alerts = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Enable Performance Alerts",
        help_text="Send alerts when system performance degrades"
    )

    performance_threshold = forms.FloatField(
        min_value=0.1,
        max_value=10.0,
        initial=2.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.1',
            'max': '10.0',
            'step': '0.1'
        }),
        label="Performance Threshold (seconds)",
        help_text="Alert when average response time exceeds this threshold"
    )


class AnalyticsFilterForm(forms.Form):
    """Form for filtering analytics data."""
    TIME_RANGES = [
        ('7', 'Last 7 days'),
        ('30', 'Last 30 days'),
        ('90', 'Last 90 days'),
        ('180', 'Last 6 months'),
        ('365', 'Last year'),
        ('custom', 'Custom range'),
    ]

    time_range = forms.ChoiceField(
        choices=TIME_RANGES,
        initial='30',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Time Range"
    )

    event_type = forms.ChoiceField(
        required=False,
        choices=[],  # Will be populated dynamically
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Event Type"
    )

    user = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by user name or email'
        }),
        label="User"
    )

    item_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Items'),
            ('book', 'Books Only'),
            ('document', 'Documents Only'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Item Type"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate event type choices from model
        from .models import AnalyticsEvent
        event_choices = [('', 'All Event Types')] + list(AnalyticsEvent.EVENT_TYPES)
        self.fields['event_type'].choices = event_choices


class SystemHealthFilterForm(forms.Form):
    """Form for filtering system health data."""
    hours = forms.IntegerField(
        min_value=1,
        max_value=168,  # 7 days
        initial=24,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '168'
        }),
        label="Hours to Display"
    )

    show_errors_only = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Show Only Records with Errors"
    )

    metric_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Metrics'),
            ('response_time', 'Response Time'),
            ('cpu_usage', 'CPU Usage'),
            ('memory_usage', 'Memory Usage'),
            ('disk_usage', 'Disk Usage'),
            ('db_connections', 'Database Connections'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Filter by Metric"
    )
