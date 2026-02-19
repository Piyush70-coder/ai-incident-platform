import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "incident_management.settings")
django.setup()

from incidents.services.similarity_service import find_similar_incidents_db

results = find_similar_incidents_db(
    "Database connection timeout error"
)

for incident, score in results:
    print(incident.title, "=>", round(score, 2))
