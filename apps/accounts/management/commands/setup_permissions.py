from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.apps import apps


class Command(BaseCommand):
    help = 'Set up user groups and permissions for the library system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up user groups and permissions...')

        # Define group configurations
        group_configs = {
            'Patron': {
                'apps': [],
                'permissions': [
                    # Catalog view permissions
                    'catalog.view_book',
                    'catalog.view_bookcopy',
                    'catalog.view_author',
                    'catalog.view_publisher',
                    'catalog.view_genre',
                    'catalog.view_topic',
                    'catalog.view_department',
                    'catalog.view_faculty',
                    # Circulation permissions for personal use
                    'circulation.view_loan',
                    'circulation.change_loan',  # for renewals
                    'circulation.add_reservation',
                    'circulation.view_reservation',
                    'circulation.change_reservation',  # for cancellation
                    'circulation.view_fine',
                    # Accounts for profile
                    'accounts.view_libraryuser',
                    'accounts.change_libraryuser',
                ]
            },
            'Staff': {
                'apps': [],  # Staff should not have full app access
                'permissions': [
                    # Attendance permissions
                    'circulation.add_attendance',
                    'circulation.change_attendance',
                    'circulation.view_attendance',
                    # Document viewing permissions (will be checked via DocumentPermission model)
                    'repository.view_document',
                    'repository.view_collection',
                    # Catalog view permissions (same as Patron)
                    'catalog.view_book',
                    'catalog.view_bookcopy',
                    'catalog.view_author',
                    'catalog.view_publisher',
                    'catalog.view_genre',
                    'catalog.view_topic',
                    'catalog.view_department',
                    'catalog.view_faculty',
                    # Circulation permissions for personal use (same as Patron)
                    'circulation.view_loan',
                    'circulation.change_loan',  # for renewals
                    'circulation.add_reservation',
                    'circulation.view_reservation',
                    'circulation.change_reservation',  # for cancellation
                    'circulation.view_fine',
                    # Basic account permissions for profile
                    'accounts.view_libraryuser',
                    'accounts.change_libraryuser',
                ]
            },
            'Admin': {
                'apps': ['accounts', 'catalog', 'circulation', 'repository', 'blog', 'events'],
                'permissions': []
            }
        }

        # Get all permissions for specified apps
        for group_name, config in group_configs.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(f'Created group: {group_name}')
            else:
                # Clear existing permissions
                group.permissions.clear()
                self.stdout.write(f'Updating group: {group_name}')

            # Add permissions for each app
            for app_label in config['apps']:
                try:
                    app_config = apps.get_app_config(app_label)
                    models = app_config.get_models()

                    for model in models:
                        # Add all permissions for the model
                        perms = Permission.objects.filter(
                            content_type__app_label=app_label,
                            content_type__model=model._meta.model_name
                        )
                        group.permissions.add(*perms)
                        self.stdout.write(f'  Added permissions for {app_label}.{model._meta.model_name}')

                except LookupError:
                    self.stdout.write(self.style.WARNING(f'App {app_label} not found, skipping'))

            # Add specific permissions
            for perm_codename in config['permissions']:
                try:
                    app_label, codename = perm_codename.split('.', 1)
                    perm = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    group.permissions.add(perm)
                    self.stdout.write(f'  Added permission: {perm_codename}')
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Permission {perm_codename} not found'))
                except ValueError:
                    self.stdout.write(self.style.WARNING(f'Invalid permission format: {perm_codename}'))

        # Clear permissions for groups not in our configuration
        configured_groups = set(group_configs.keys())
        for group in Group.objects.all():
            if group.name not in configured_groups:
                group.permissions.clear()
                self.stdout.write(f'Cleared permissions for unused group: {group.name}')

        self.stdout.write(self.style.SUCCESS('User groups and permissions setup completed!'))

        # Display summary
        self.stdout.write('\nGroup Summary:')
        for group in Group.objects.all():
            perm_count = group.permissions.count()
            self.stdout.write(f'  {group.name}: {perm_count} permissions')
