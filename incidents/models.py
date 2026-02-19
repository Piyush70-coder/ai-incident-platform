from django.db import models
from django.conf import settings
from companies.models import Company
import uuid


# =====================================================
# INCIDENT
# =====================================================

class Incident(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('investigating', 'Investigating'),
        ('analyzing', 'Analyzing'),
        ('root_cause_found', 'Root Cause Found'),
        ('mitigating', 'Mitigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    CATEGORY_CHOICES = [
        ('database', 'Database'),
        ('network', 'Network'),
        ('application', 'Application'),
        ('infrastructure', 'Infrastructure'),
        ('security', 'Security'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="incidents"
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        blank=True
    )

    affected_services = models.JSONField(default=list, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_incidents"
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_incidents"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="For planned maintenance"
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.severity})"

    @property
    def incident_id(self):
        return str(self.id).split('-')[0].upper()


# =====================================================
# INCIDENT LOGS
# =====================================================

class IncidentLog(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="logs"
    )

    file = models.FileField(upload_to="incident_logs/")
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=50)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    processed = models.BooleanField(default=False)
    processed_content = models.TextField(blank=True)

    def __str__(self):
        return f"{self.file_name} - {self.incident.title}"


# =====================================================
# INCIDENT EMBEDDING (MiniLM)
# =====================================================

class IncidentEmbedding(models.Model):
    incident = models.OneToOneField(
        Incident,
        on_delete=models.CASCADE,
        related_name="embedding"
    )

    vector = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Embedding for {self.incident.incident_id}"


# =====================================================
# AI INCIDENT ANALYSIS (ROOT CAUSE + POSTMORTEM)
# =====================================================

class IncidentAnalysis(models.Model):
    AI_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    incident = models.OneToOneField(
        Incident,
        on_delete=models.CASCADE,
        related_name="analysis"
    )

    # ---- Core AI Outputs ----
    root_cause = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    postmortem = models.TextField(blank=True, null=True)

    confidence_score = models.FloatField(default=0.0)

    # ---- Optional structured outputs ----
    timeline = models.TextField(blank=True)
    severity = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=20, blank=True)

    affected_services = models.TextField(blank=True)
    mitigation_steps = models.TextField(blank=True)
    fix_steps = models.TextField(blank=True)

    # ---- AI Meta ----
    ai_status = models.CharField(
        max_length=20,
        choices=AI_STATUS_CHOICES,
        default="pending"
    )
    error_message = models.TextField(blank=True)

    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Analysis - {self.incident.title}"

    @property
    def affected_services_list(self):
        if not self.affected_services:
            return []
        return [s.strip() for s in self.affected_services.split(",") if s.strip()]

    @property
    def fix_steps_list(self):
        if not self.fix_steps:
            return []
        return self.fix_steps.splitlines()


# =====================================================
# SIMILAR INCIDENTS (MiniLM similarity)
# =====================================================

class SimilarIncident(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="similar_incidents"
    )
    similar_to = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="similar_from"
    )

    similarity_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('incident', 'similar_to')
        ordering = ['-similarity_score']

    def __str__(self):
        return f"{self.incident.title} ~ {self.similar_to.title}"


# =====================================================
# COMMENTS
# =====================================================

class IncidentComment(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    comment = models.TextField()
    attachments = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.incident.title}"


# =====================================================
# INCIDENT TIMELINE
# =====================================================

class IncidentTimeline(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('assigned', 'Assigned'),
        ('status_changed', 'Status Changed'),
        ('commented', 'Commented'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="timeline_entries"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    from_state = models.CharField(max_length=20, blank=True)
    to_state = models.CharField(max_length=20, blank=True)

    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.incident.title}"


# =====================================================
# NOTIFICATIONS
# =====================================================

class Notification(models.Model):
    TYPE_CHOICES = [
        ('incident_created', 'Incident Created'),
        ('incident_assigned', 'Incident Assigned'),
        ('incident_updated', 'Incident Updated'),
        ('incident_resolved', 'Incident Resolved'),
        ('comment_added', 'Comment Added'),
        ('status_changed', 'Status Changed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message[:40]}"
