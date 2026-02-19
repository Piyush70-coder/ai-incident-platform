# Generated migration for severity, affected_services, and fix_steps as TextField

from django.db import migrations, models
import json


def convert_fix_steps_to_text(apps, schema_editor):
    IncidentAnalysis = apps.get_model('incidents', 'IncidentAnalysis')
    for analysis in IncidentAnalysis.objects.all():
        if hasattr(analysis, 'fix_steps') and analysis.fix_steps:
            if isinstance(analysis.fix_steps, (list, dict)):
                analysis.fix_steps = json.dumps(analysis.fix_steps)
                analysis.save(update_fields=['fix_steps'])


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0003_incidentanalysis_ai_status_error_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidentanalysis',
            name='severity',
            field=models.CharField(blank=True, help_text='AI-detected severity', max_length=20),
        ),
        migrations.AddField(
            model_name='incidentanalysis',
            name='affected_services',
            field=models.TextField(blank=True, help_text='Affected services (JSON array as string)'),
        ),
        migrations.RunPython(convert_fix_steps_to_text, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='incidentanalysis',
            name='fix_steps',
            field=models.TextField(blank=True, help_text='Structured remediation steps (JSON array as string)'),
        ),
    ]

