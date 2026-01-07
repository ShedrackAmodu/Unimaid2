from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.accounts.models import LibraryUser


class Command(BaseCommand):
    help = 'Assign groups to existing users based on membership_type'

    def handle(self, *args, **options):
        self.stdout.write('Assigning groups to existing users...')

        users = LibraryUser.objects.all()
        updated_count = 0

        for user in users:
            old_groups = list(user.groups.all())
            user.assign_group_based_on_membership()
            new_groups = list(user.groups.all())

            if old_groups != new_groups:
                updated_count += 1
                self.stdout.write(f'Updated {user.username}: {user.membership_type} -> {[g.name for g in new_groups]}')

        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} users'))

        # Show summary
        self.stdout.write('\nGroup assignment summary:')
        for group in Group.objects.all():
            count = group.user_set.count()
            self.stdout.write(f'  {group.name}: {count} users')
