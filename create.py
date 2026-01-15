import os
import django
from django.core.management import call_command

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import LibraryUser

def main():
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

if __name__ == '__main__':
    main()
