import os
import django
from datetime import timedelta
from django.utils import timezone
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')
django.setup()

from incidents.models import Incident
from companies.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()

def populate_resolved_data():
    print("--- Populating Resolved Data ---")
    
    # Get context
    company = Company.objects.first()
    if not company:
        print("No company found.")
        return

    user = User.objects.first()
    
    # Find some 'new' or 'investigating' incidents and resolve them
    candidates = Incident.objects.filter(company=company, status__in=['new', 'investigating'])[:5]
    
    if not candidates.exists():
        print("No candidates found to resolve.")
        # Create one
        Incident.objects.create(
            title="Resolved Test Incident",
            description="This is a test incident to show resolved status.",
            company=company,
            created_by=user,
            severity="medium",
            status="resolved",
            resolved_at=timezone.now()
        )
        print("Created new resolved incident.")
    else:
        for incident in candidates:
            # Randomly set resolution time between 1 and 24 hours ago
            created_time = incident.created_at
            resolution_time = created_time + timedelta(hours=random.uniform(0.5, 48))
            
            # Ensure resolution time is in the past
            if resolution_time > timezone.now():
                resolution_time = timezone.now()
            
            incident.status = 'resolved'
            incident.resolved_at = resolution_time
            incident.save()
            print(f"Resolved incident {incident.id} ({incident.title})")

    print("Done. Dashboard should now show data.")

if __name__ == "__main__":
    populate_resolved_data()
