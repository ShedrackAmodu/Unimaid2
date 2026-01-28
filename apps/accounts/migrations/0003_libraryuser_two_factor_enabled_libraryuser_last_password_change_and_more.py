# Generated manually to fix OperationalError for missing fields

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_libraryuser_office_hours_libraryuser_position_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="libraryuser",
            name="two_factor_enabled",
            field=models.BooleanField(default=False, help_text="Whether two-factor authentication is enabled"),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="last_password_change",
            field=models.DateTimeField(auto_now_add=True, help_text="When the password was last changed"),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="failed_login_attempts",
            field=models.PositiveIntegerField(default=0, help_text="Number of failed login attempts"),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="locked_until",
            field=models.DateTimeField(blank=True, help_text="Account locked until this time due to failed attempts", null=True),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="last_activity",
            field=models.DateTimeField(auto_now=True, help_text="Last time user was active"),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="alternate_phone",
            field=models.CharField(blank=True, help_text="Alternate phone number", max_length=20),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="address",
            field=models.TextField(blank=True, help_text="Physical address"),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="emergency_contact_name",
            field=models.CharField(blank=True, help_text="Emergency contact person name", max_length=100),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="emergency_contact_relation",
            field=models.CharField(blank=True, help_text="Relationship to emergency contact", max_length=50),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="emergency_contact_phone",
            field=models.CharField(blank=True, help_text="Emergency contact phone number", max_length=20),
        ),
        migrations.AddField(
            model_name="libraryuser",
            name="emergency_contact_email",
            field=models.EmailField(blank=True, help_text="Emergency contact email address", max_length=254),
        ),
    ]