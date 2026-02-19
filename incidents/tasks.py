from celery import shared_task
from django.db import transaction
from django.utils import timezone

from incidents.models import Incident, IncidentAnalysis, IncidentLog
from incidents.services.embedding_service import save_incident_embedding
from incidents.services.context_builder_simple import (
    build_incident_context_with_similarity
)
from incidents.services.text_generation import generate_root_cause
from incidents.services.ai_parser import parse_ai_output
from incidents.services.postmortem_service import generate_postmortem
from incidents.services.log_processor import process_log_file


# =========================================================
# STEP 1: GENERATE EMBEDDING (MiniLM)
# =========================================================
@shared_task
def generate_incident_embedding(incident_id):
    """
    Incident title → MiniLM embedding → DB save
    """
    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        return

    save_incident_embedding(incident, incident.title)


# =========================================================
# STEP 2: ROOT CAUSE ANALYSIS (FLAN-T5)
# =========================================================
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 3},
)
def generate_root_cause_analysis(self, incident_id):
    """
    Incident → Similar Incidents → Context → FLAN-T5 → Parsed RCA
    """
    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        return

    analysis, _ = IncidentAnalysis.objects.get_or_create(
        incident=incident,
        defaults={"ai_status": "pending"}
    )

    try:
        # 1️⃣ Build context (logs + similar incidents)
        context = build_incident_context_with_similarity(incident)

        # 2️⃣ Generate raw AI output
        ai_result = generate_root_cause(context)
        raw_output = ai_result.get("raw", "")

        # 3️⃣ Parse AI output
        root_cause, explanation, ai_confidence = parse_ai_output(raw_output)

        # 4️⃣ Heuristic Confidence Calculation
        final_confidence = 0.30  # Base confidence

        # Keyword heuristics (Infra-specific)
        infra_keywords = ['redis', 'database', 'postgres', 'dns', 'cpu', 'memory', 'disk', 'network', 'kafka', 'queue', '504', '502', 'timeout']
        if any(k in root_cause.lower() for k in infra_keywords):
            final_confidence += 0.20
        
        # Log evidence heuristic (Timestamps / Errors)
        # Check for typical timestamp patterns or 'error' keyword in context
        if "error" in context.lower() or "exception" in context.lower():
            final_confidence += 0.10
        
        # Similarity heuristic
        if incident.similar_incidents.exists():
            final_confidence += 0.15

        # Cap confidence at strict 0.85
        final_confidence = min(0.85, final_confidence)

        # 5️⃣ Save analysis atomically
        with transaction.atomic():
            analysis.root_cause = root_cause
            analysis.explanation = explanation
            analysis.confidence_score = final_confidence
            analysis.ai_status = "completed"
            analysis.error_message = ""
            analysis.completed_at = timezone.now()
            analysis.save()

    except Exception as e:
        analysis.ai_status = "failed"
        analysis.error_message = str(e)[:500]
        analysis.save()
        raise


# =========================================================
# STEP 3: POSTMORTEM GENERATION
# =========================================================
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 3},
)
def generate_postmortem_report(self, incident_id):
    """
    Incident + RCA → AI Postmortem
    """
    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        return

    analysis, _ = IncidentAnalysis.objects.get_or_create(incident=incident)

    try:
        context = build_incident_context_with_similarity(incident)
        
        # Use existing analysis data if available
        root_cause = analysis.root_cause
        explanation = analysis.explanation
        
        report = generate_postmortem(context, root_cause, explanation)

        analysis.postmortem = report
        analysis.save()

    except Exception as e:
        analysis.error_message = str(e)[:500]
        analysis.save()
        raise


# =========================================================
# STEP 4: PROCESS INCIDENT LOGS
# =========================================================
@shared_task
def process_incident_logs(incident_id):
    """
    Ensure all logs for an incident are processed and content extracted.
    """
    try:
        logs = IncidentLog.objects.filter(incident_id=incident_id, processed=False)
        for log in logs:
            try:
                processed_content = process_log_file(log)
                if processed_content:
                    log.processed_content = processed_content
                    log.processed = True
                    log.save(update_fields=['processed_content', 'processed'])
            except Exception as e:
                # Log error but continue processing other logs
                print(f"Error processing log {log.id}: {e}")
    except Exception as e:
        print(f"Error in process_incident_logs task: {e}")
