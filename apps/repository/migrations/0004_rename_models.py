# Simple migration to rename Document models to EBook
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0003_documentpermissionrequest'),
    ]

    operations = [
        # Rename the models (tables will be renamed automatically)
        migrations.RenameModel(
            old_name='Document',
            new_name='EBook',
        ),

        migrations.RenameModel(
            old_name='DocumentPermissionRequest',
            new_name='EBookPermissionRequest',
        ),

        migrations.RenameModel(
            old_name='DocumentPermission',
            new_name='EBookPermission',
        ),
    ]
