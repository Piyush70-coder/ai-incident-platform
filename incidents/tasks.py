from celery import shared_task
from django.db import transaction
from django.utils import timezone

from incidents.models import Incident, IncidentAnalysis, IncidentLog
from incidents.services.embedding_service import save_incident_embedding
from incidents.services.context_builder_simple import (
    build_incident_context_with_similarity
)
from incidents.services.text_generation import generate_root_cause
from incidents.services.postmortem_service import generate_postmortem
from incidents.services.log_processor import process_log_file
from incidents.services.log_processor import extract_smart_context
from incidents.services import ai_parser


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

        # 2️⃣ Filter context to prevent LLM overflow and avoid sending full raw logs
        smart_context = extract_smart_context(context)

        # 3️⃣ Generate structured AI output (Groq / Llama)
        ai_result = generate_root_cause(smart_context)
        raw_output = ai_result.get("raw", "")
        llm_error = ai_result.get("error")
        if llm_error:
            raise RuntimeError(llm_error)

        parsed = ai_parser.parse_sre_structured_output(raw_output or "{}", extra_context=smart_context)
        payload = parsed["payload"]
        final_confidence = float(parsed["confidence_score"])
        severity_label = parsed.get("severity") or ""

        if parsed.get("is_error_response"):
            with transaction.atomic():
                analysis.root_cause = ""
                analysis.explanation = str(parsed.get("explanation") or "")
                analysis.confidence_score = 0.0
                analysis.severity = ""
                analysis.structured_output = payload
                analysis.full_ai_report = payload
                analysis.ai_status = "completed"
                analysis.error_message = ""
                analysis.save()
            return

        if not parsed.get("root_cause"):
            raise ValueError("AI response missing primary root cause")

        # 6️⃣ Save analysis atomically
        with transaction.atomic():
            analysis.root_cause = str(parsed["root_cause"])
            analysis.explanation = str(parsed.get("explanation") or "")
            analysis.confidence_score = final_confidence
            analysis.severity = severity_label
            analysis.structured_output = payload
            analysis.full_ai_report = payload

            # Remediation mapping
            resolutions = payload.get("prioritized_resolutions", {})
            imm = resolutions.get("P0_immediate") or payload.get("immediate_fixes")
            if isinstance(imm, list):
                analysis.mitigation_steps = "\n".join(f"- {s}" for s in imm if str(s).strip())

            tactical = resolutions.get("P1_tactical", []) or payload.get("root_fixes", [])
            prev = resolutions.get("P2_prevention", []) or payload.get("prevention_steps", [])
            cmds = payload.get("safe_commands", [])
            fix_parts = []
            if isinstance(tactical, list) and tactical:
                fix_parts.append("Priority P1 (Tactical Fixes):\n" + "\n".join(f"- {s}" for s in tactical))
            if isinstance(prev, list) and prev:
                fix_parts.append("Priority P2 (Prevention):\n" + "\n".join(f"- {s}" for s in prev))
            if isinstance(cmds, list) and cmds:
                fix_parts.append("Safe Commands:\n" + "\n".join(f"  {s}" for s in cmds))
            analysis.fix_steps = "\n\n".join(fix_parts)

            # Build Postmortem from new schema
            pm_parts = [
                f"Summary: {payload.get('analysis_summary', '')}",
                f"Failure Chain: {payload.get('failure_chain', '')}",
                f"Root Cause: {parsed['root_cause']}"
            ]
            
            depth = payload.get("root_cause_depth", [])
            if depth:
                pm_parts.append("Technical Depth Analysis:\n" + "\n".join(f"- [{d.get('component')}] {d.get('failure')}: {d.get('why')}" for d in depth))

            if imm:
                pm_parts.append("P0 Immediate Actions:\n" + "\n".join(f"- {s}" for s in imm))
            if tactical:
                pm_parts.append("P1 Root Fixes:\n" + "\n".join(f"- {s}" for s in tactical))
            
            analysis.postmortem = "\n\n".join(p for p in pm_parts if p.strip())
            
            analysis.ai_status = "completed"
            analysis.error_message = ""
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
def process_incident_logs(incident_id, trigger_ai=True):
    """
    Ensure all logs for an incident are processed and content extracted.
    After masking/saving processed logs, optionally queue root-cause analysis.
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
        return

    if trigger_ai:
        generate_root_cause_analysis.delay(incident_id)
