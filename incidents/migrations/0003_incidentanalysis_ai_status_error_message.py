# Generated migration for AI status tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0002_incidentanalysis_fix_steps'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidentanalysis',
            name='ai_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')],
                default='pending',
                help_text='AI analysis status',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='incidentanalysis',
            name='error_message',
            field=models.TextField(blank=True, help_text='Error message if AI analysis failed'),
        ),
    ]

