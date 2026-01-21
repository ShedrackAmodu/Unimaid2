import os
import django
from django.core.management import call_command

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import LibraryUser

def main():
    # Load backup data if exists
    if os.path.exists('backup.json'):
        print("Loading data from backup.json...")
        try:
            call_command('loaddata', 'backup')
            print("Data loaded from backup.json successfully.")
        except Exception as e:
            print(f"Error loading data from backup.json: {e}")
            return
    else:
        print("No backup.json found, proceeding with fresh setup.")

    print("Running makemigrations...")
    try:
        call_command('makemigrations')
        print("Makemigrations completed successfully.")
    except Exception as e:
        print(f"Error running makemigrations: {e}")
        return

    print("Running migrate...")
    try:
        call_command('migrate')
        print("Migrate completed successfully.")
    except Exception as e:
        print(f"Error running migrate: {e}")
        return

    print("Setting up user permissions...")
    try:
        call_command('setup_permissions')
        print("User permissions setup completed successfully.")
    except Exception as e:
        print(f"Error setting up permissions: {e}")
        return

    print("Running collectstatic...")
    try:
        call_command('collectstatic', '--noinput')
        print("Collectstatic completed successfully.")
    except Exception as e:
        print(f"Error running collectstatic: {e}")
        return

    print("Creating superuser...")
    try:
        if not LibraryUser.objects.filter(username='drmk').exists():
            LibraryUser.objects.create_superuser('drmk', '', 'drmk')
            print("Superuser 'drmk' created successfully.")
        else:
            print("Superuser 'drmk' already exists.")
    except Exception as e:
        print(f"Error creating superuser: {e}")

    # Backup data to JSON
    print("Backing up data to backup.json...")
    try:
        call_command('dumpdata', '--output', 'backup.json')
        print("Data backed up to backup.json successfully.")
    except Exception as e:
        print(f"Error backing up data: {e}")

if __name__ == '__main__':
    main()
