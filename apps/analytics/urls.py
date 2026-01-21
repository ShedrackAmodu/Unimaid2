from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main dashboard
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='dashboard_alt'),

    # Reports
    path('reports/', views.analytics_reports_view, name='reports'),
    path('reports/generate/', views.analytics_reports_view, name='generate_report'),

    # System health
    path('system-health/', views.system_health_view, name='system_health'),

    # Event analytics
    path('events/', views.event_analytics_view, name='event_analytics'),

    # Settings
    path('settings/', views.analytics_settings_view, name='settings'),

    # Data export
    path('export/', views.export_analytics_data, name='export_data'),
]
