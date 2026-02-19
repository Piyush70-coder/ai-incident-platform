import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')
django.setup()
from incidents.models import Incident

total = Incident.objects.count()
resolved = Incident.objects.filter(status='resolved').count()
resolved_with_time = Incident.objects.filter(resolved_at__isnull=False).count()
resolved_no_time = Incident.objects.filter(status='resolved', resolved_at__isnull=True).count()

print(f'Total: {total}')
print(f'Resolved Status: {resolved}')
print(f'Resolved with Time: {resolved_with_time}')
print(f'Resolved Status but No Time: {resolved_no_time}')

if resolved_no_time > 0:
    print('Sample resolved incidents without resolved_at:')
    for i in Incident.objects.filter(status='resolved', resolved_at__isnull=True)[:5]:
        print(f'- {i.id}: {i.title}')
