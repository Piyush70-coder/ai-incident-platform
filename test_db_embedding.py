import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "incident_management.settings")
django.setup()

from incidents.models import Incident
from incidents.services.embedding_service import save_incident_embedding

incident = Incident.objects.first()

if incident:
    save_incident_embedding(incident, "Database timeout during peak traffic")
    print("Embedding saved successfully")
else:
    print("No incident found")
