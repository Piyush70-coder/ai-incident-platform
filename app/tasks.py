from celery import shared_task
from django.db import transaction
from incidents.models import Incident, IncidentAnalysis



@shared_task(name="analyze_incident_logs")
def analyze_incident_logs(incident_id: str):
    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        return

    analyzer = GeminiAnalyzerService()
    result = analyzer.analyze(incident)

    with transaction.atomic():
        # Auto-update incident fields
        if result.get("title"):
            incident.title = result["title"]
        if result.get("severity") in dict(Incident.SEVERITY_CHOICES):
            incident.severity = result["severity"]
        if isinstance(result.get("affected_services"), list):
            incident.affected_services = result["affected_services"]
        incident.save()

        # Save analysis
        IncidentAnalysis.objects.update_or_create(
            incident=incident,
            defaults={
                "root_cause": result.get("root_cause", ""),
                "mitigation_steps": "",
                "confidence_score": 0.7,
            },
        )
