from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json
import tempfile

from .models import (
    Incident, IncidentLog, IncidentAnalysis, IncidentTimeline, Notification
)
from .forms import IncidentForm, IncidentCommentForm
from .services.analytics import AnalyticsService
from .services.notifications import NotificationService
from .tasks import (
    generate_incident_embedding,
    generate_root_cause_analysis,
    generate_postmortem_report,
    process_incident_logs
)

from django.http import FileResponse
from incidents.services.postmortem_export import (
    export_postmortem_markdown,
    export_postmortem_pdf
)

# =========================================================
# DASHBOARD
# =========================================================
@login_required
def dashboard_view(request):
    company = request.company
    if not company:
        messages.error(request, "You must be associated with a company.")
        return redirect('profile')

    analytics = AnalyticsService()
    metrics = analytics.get_dashboard_metrics(company)
    timeseries = analytics.get_incidents_timeseries(company, days=30)

    recent_incidents = Incident.objects.filter(
        company=company
    ).order_by('-created_at')[:10]

    context = {
        'metrics': metrics,
        'timeseries': json.dumps(list(timeseries), cls=DjangoJSONEncoder),
        'recent_incidents': recent_incidents,
        'metrics_json': json.dumps(metrics, cls=DjangoJSONEncoder),
    }
    return render(request, 'incidents/dashboard.html', context)


# =========================================================
# INCIDENT LIST
# =========================================================
@login_required
def incident_list_view(request):
    company = request.company
    if not company:
        messages.error(request, "You must be associated with a company.")
        return redirect('profile')

    incidents = Incident.objects.filter(company=company)

    status = request.GET.get('status')
    severity = request.GET.get('severity')
    search = request.GET.get('search')

    if status:
        incidents = incidents.filter(status=status)
    if severity:
        incidents = incidents.filter(severity=severity)
    if search:
        incidents = incidents.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    paginator = Paginator(incidents.order_by('-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'incidents/list.html', {'page_obj': page_obj})


# =========================================================
# CREATE INCIDENT
# =========================================================
@login_required
def incident_create_view(request):
    company = request.company
    if not company:
        messages.error(request, "You must be associated with a company.")
        return redirect('profile')

    if request.method == 'POST':
        form = IncidentForm(request.POST, request.FILES, company=company)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.company = company
            incident.created_by = request.user
            incident.save()

            IncidentTimeline.objects.create(
                incident=incident,
                user=request.user,
                action='created',
                comment=f'Incident created: {incident.title}'
            )

            # Process and save log files
            from incidents.services.log_processor import process_log_file
            for file in request.FILES.getlist('log_files'):
                log = IncidentLog.objects.create(
                    incident=incident,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    file_type=file.name.split('.')[-1]
                )
                # Process log content immediately
                try:
                    processed_content = process_log_file(log)
                    if processed_content:
                        log.processed_content = processed_content
                        log.processed = True
                        log.save(update_fields=['processed_content', 'processed'])
                except Exception as e:
                    # Log error but don't fail incident creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to process log {log.file_name}: {str(e)}")

            # 🔥 IMPORTANT: create analysis row immediately
            IncidentAnalysis.objects.get_or_create(
                incident=incident,
                defaults={"ai_status": "pending"}
            )

            # 🔥 AI PIPELINE
            # Process logs first, then generate analysis
            process_incident_logs.delay(str(incident.id))
            generate_incident_embedding.delay(str(incident.id))
            # Delay root cause analysis slightly to ensure logs are processed
            generate_root_cause_analysis.apply_async(
                args=[str(incident.id)],
                countdown=5  # Wait 5 seconds for logs to process
            )
            generate_postmortem_report.apply_async(
                args=[str(incident.id)],
                countdown=10  # Wait 10 seconds for root cause analysis
            )

            NotificationService.notify_incident_created(incident)
            messages.success(request, "Incident created successfully!")
            return redirect('incident_detail', incident_id=incident.id)
    else:
        form = IncidentForm(company=company)

    return render(request, 'incidents/create.html', {'form': form})


# =========================================================
# INCIDENT DETAIL
# =========================================================
@login_required
def incident_detail_view(request, incident_id):
    company = request.company
    if not company:
        return redirect('profile')

    incident = get_object_or_404(Incident, id=incident_id, company=company)

    # 🔥 ensure analysis always exists
    analysis, _ = IncidentAnalysis.objects.get_or_create(
        incident=incident,
        defaults={"ai_status": "pending"}
    )

    from .services.timeline import build_timeline
    technical_timeline = build_timeline(incident.logs.all())

    return render(
        request,
        'incidents/detail.html',
        {
            'incident': incident,
            'analysis': analysis,
            'technical_timeline': technical_timeline,
            'comments': incident.comments.all(),
            'comment_form': IncidentCommentForm(),
        }
    )


# =========================================================
# MANUAL AI TRIGGER
# =========================================================
@login_required
@require_http_methods(["POST"])
def trigger_ai_analysis(request, incident_id):
    company = request.company
    if not company:
        return JsonResponse({"error": "No company"}, status=403)
    
    incident = get_object_or_404(Incident, id=incident_id, company=company)

    # Process logs first if not processed
    process_incident_logs.delay(str(incident.id))

    IncidentAnalysis.objects.update_or_create(
        incident=incident,
        defaults={"ai_status": "pending", "error_message": ""}
    )

    # Trigger analysis with delays to ensure logs are processed
    generate_root_cause_analysis.apply_async(
        args=[str(incident.id)],
        countdown=3
    )
    generate_postmortem_report.apply_async(
        args=[str(incident.id)],
        countdown=8
    )

    return JsonResponse({"status": "AI analysis started", "message": "Analysis will complete in a few moments"})


# =========================================================
# LOG VIEWER
# =========================================================
@login_required
def log_viewer_view(request, log_id):
    log = get_object_or_404(IncidentLog, id=log_id)
    return render(
        request,
        'incidents/log_viewer.html',
        {'log': log, 'content': log.processed_content or ""}
    )


# =========================================================
# POSTMORTEM DOWNLOADS
# =========================================================
@login_required
def download_postmortem_md(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    filename, content = export_postmortem_markdown(incident)

    response = HttpResponse(content, content_type="text/markdown")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def download_postmortem_pdf(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        export_postmortem_pdf(incident, tmp.name)
        return FileResponse(
            open(tmp.name, "rb"),
            as_attachment=True,
            filename=f"postmortem_{incident.id}.pdf"
        )


# =========================================================
# PAST INCIDENTS
# =========================================================
@login_required
def past_incidents_view(request):
    company = request.company
    if not company:
        messages.error(request, "You must be associated with a company.")
        return redirect('profile')

    incidents = Incident.objects.filter(
        company=company,
        status__in=["resolved", "closed"]
    ).order_by("-created_at")

    paginator = Paginator(incidents, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "incidents/past_incidents.html", {"page_obj": page_obj})


# =========================================================
# LOG EXPLORER
# =========================================================
@login_required
def log_explorer_view(request):
    recent_logs = IncidentLog.objects.select_related(
        'incident'
    ).order_by('-uploaded_at')[:20]

    return render(
        request,
        'incidents/log_explorer.html',
        {'recent_logs': recent_logs}
    )


# =========================================================
# NOTIFICATIONS
# =========================================================
@login_required
def notifications_view(request):
    if request.method == 'POST':
        if 'mark_all_read' in request.POST:
            request.user.notifications.filter(read=False).update(read=True)
            messages.success(request, 'All notifications marked as read.')
        elif 'mark_read' in request.POST:
            notification_id = request.POST.get('notification_id')
            if notification_id:
                notification = get_object_or_404(Notification, id=notification_id, user=request.user)
                notification.read = True
                notification.save()
                messages.success(request, 'Notification marked as read.')
        return redirect('notifications')

    return render(
        request,
        'incidents/notifications.html',
        {'notifications': request.user.notifications.all()[:50]}
    )



from django.views.decorators.http import require_http_methods
from incidents.services.text_generation import generate_root_cause

@login_required
@require_http_methods(["POST"])
def ai_explain_logs(request):
    log_content = request.POST.get("log_content", "")
    if not log_content:
        return HttpResponse("No log content provided")

    result = generate_root_cause(log_content)
    explanation = result.get("raw", "")

    return HttpResponse(
        f"<pre class='whitespace-pre-wrap'>{explanation}</pre>"
    )


# =========================================================
# INCIDENT UPDATE VIEW (FIX FOR CELERY ERROR)
# =========================================================
from django.views.decorators.http import require_POST

@login_required
@require_POST
def incident_update_view(request, incident_id):
    company = request.company
    if not company:
        return JsonResponse({"error": "No company"}, status=403)

    incident = get_object_or_404(
        Incident,
        id=incident_id,
        company=company
    )

    old_status = incident.status
    new_status = request.POST.get("status")

    if new_status and new_status in dict(Incident.STATUS_CHOICES):
        incident.status = new_status

        if new_status == "resolved" and not incident.resolved_at:
            incident.resolved_at = timezone.now()

        IncidentTimeline.objects.create(
            incident=incident,
            user=request.user,
            action="status_changed",
            from_state=old_status,
            to_state=new_status,
        )

        NotificationService.notify_status_changed(
            incident, request.user, old_status, new_status
        )

    incident.save()
    messages.success(request, "Incident updated successfully")
    return redirect("incident_detail", incident_id=incident.id)

# =========================================================
# ANALYTICS API VIEW (FIX FOR CELERY)
# =========================================================
@login_required
def analytics_api_view(request):
    company = request.company
    if not company:
        return JsonResponse({"error": "No company"}, status=403)

    analytics = AnalyticsService()

    return JsonResponse({
        "metrics": analytics.get_dashboard_metrics(company),
        "timeseries": list(
            analytics.get_incidents_timeseries(company, days=30)
        ),
    })
