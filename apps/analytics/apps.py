from django.apps import AppConfig
import os


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    path = os.path.dirname(os.path.abspath(__file__))
