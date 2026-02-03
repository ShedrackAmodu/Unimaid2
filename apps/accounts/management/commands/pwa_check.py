"""
Django management command to verify and setup PWA
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import json


class Command(BaseCommand):
    help = 'Verify and setup Progressive Web App (PWA) configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check if PWA is properly configured',
        )
        parser.add_argument(
            '--update-version',
            action='store_true',
            help='Update service worker cache version',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PWA Configuration Checker'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Check files
        self.check_pwa_files()
        
        # Check Django settings
        self.check_django_settings()
        
        # Check URLs
        self.check_urls_config()

        # Update version if requested
        if options.get('update_version'):
            self.update_cache_version()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ PWA Setup Verification Complete!'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Run: python manage.py collectstatic')
        self.stdout.write('2. Ensure HTTPS is enabled in production')
        self.stdout.write('3. Configure web server cache headers')
        self.stdout.write('4. Test offline functionality')

    def check_pwa_files(self):
        """Check if all PWA files exist"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('📋 Checking PWA Files...'))
        
        base_dir = settings.BASE_DIR
        files_to_check = {
            'Service Worker': 'static/js/service-worker.js',
            'PWA Register Script': 'static/js/pwa-register.js',
            'Web App Manifest': 'static/manifest.json',
            'Offline Page': 'templates/offline.html',
        }
        
        all_exist = True
        for name, file_path in files_to_check.items():
            full_path = os.path.join(base_dir, file_path)
            if os.path.exists(full_path):
                self.stdout.write(f'  ✅ {name}: {file_path}')
                
                # Validate manifest JSON
                if file_path.endswith('manifest.json'):
                    try:
                        with open(full_path, 'r') as f:
                            json.load(f)
                        self.stdout.write('     └─ Valid JSON ✓')
                    except json.JSONDecodeError as e:
                        self.stdout.write(
                            self.style.ERROR(f'     └─ Invalid JSON: {e}')
                        )
                        all_exist = False
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ {name}: {file_path} - NOT FOUND')
                )
                all_exist = False
        
        if not all_exist:
            raise CommandError('Some PWA files are missing!')

    def check_django_settings(self):
        """Check Django settings for PWA compatibility"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('⚙️  Checking Django Settings...'))
        
        checks = {
            'Static Files Configured': hasattr(settings, 'STATIC_URL'),
            'Static Root Set': hasattr(settings, 'STATIC_ROOT'),
            'Media Root Set': hasattr(settings, 'MEDIA_ROOT'),
            'Allowed Hosts': bool(settings.ALLOWED_HOSTS),
        }
        
        production_mode = not settings.DEBUG
        if production_mode:
            checks['HTTPS Redirect'] = getattr(
                settings, 'SECURE_SSL_REDIRECT', False
            )
            checks['Session Secure'] = getattr(
                settings, 'SESSION_COOKIE_SECURE', False
            )
            checks['CSRF Secure'] = getattr(
                settings, 'CSRF_COOKIE_SECURE', False
            )
        
        for check_name, result in checks.items():
            if result:
                self.stdout.write(f'  ✅ {check_name}')
            else:
                status = 'ℹ️  (development)' if not production_mode and check_name.startswith('HTTPS') else '⚠️  Configure for production'
                self.stdout.write(f'  {status} {check_name}')

    def check_urls_config(self):
        """Check if PWA URLs are configured"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('🔗 Checking URL Configuration...'))
        
        try:
            from django.urls import path, include
            from config.urls import urlpatterns
            
            offline_configured = False
            for pattern in urlpatterns:
                if hasattr(pattern, 'pattern'):
                    if 'offline' in str(pattern.pattern):
                        offline_configured = True
                        break
            
            if offline_configured:
                self.stdout.write('  ✅ Offline route configured')
            else:
                self.stdout.write(
                    self.style.WARNING('  ⚠️  Offline route not found in URLs')
                )
        except Exception as e:
            self.stdout.write(f'  ℹ️  Could not check URL config: {e}')

    def update_cache_version(self):
        """Update service worker cache version"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('🔄 Updating Cache Version...'))
        
        from datetime import datetime
        
        base_dir = settings.BASE_DIR
        service_worker_path = os.path.join(
            base_dir, 'static/js/service-worker.js'
        )
        
        try:
            with open(service_worker_path, 'r') as f:
                content = f.read()
            
            # Generate new version
            version = datetime.now().strftime('ramat-library-v%Y%m%d%H%M%S')
            
            # Find and replace cache name
            old_cache = content.split("const CACHE_NAME = '")[1].split("'")[0]
            new_content = content.replace(
                f"const CACHE_NAME = '{old_cache}';",
                f"const CACHE_NAME = '{version}';"
            )
            
            with open(service_worker_path, 'w') as f:
                f.write(new_content)
            
            self.stdout.write(
                f'  ✅ Cache version updated: {old_cache} → {version}'
            )
        except Exception as e:
            raise CommandError(f'Error updating cache version: {e}')
