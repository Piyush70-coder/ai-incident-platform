from django.contrib import admin
from .models import (
    Incident, IncidentLog, IncidentAnalysis, IncidentComment,
    IncidentTimeline, SimilarIncident, Notification
)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'severity', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'severity', 'category', 'company', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(IncidentLog)
class IncidentLogAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'incident', 'file_type', 'file_size', 'processed', 'uploaded_at']
    list_filter = ['processed', 'file_type', 'uploaded_at']
    search_fields = ['file_name', 'incident__title']


@admin.register(IncidentAnalysis)
class IncidentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['incident', 'confidence_score', 'category', 'analyzed_at']
    list_filter = ['category', 'analyzed_at']
    search_fields = ['incident__title', 'root_cause']


@admin.register(IncidentComment)
class IncidentCommentAdmin(admin.ModelAdmin):
    list_display = ['incident', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment', 'incident__title', 'user__username']


@admin.register(IncidentTimeline)
class IncidentTimelineAdmin(admin.ModelAdmin):
    list_display = ['incident', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['incident__title', 'comment']


@admin.register(SimilarIncident)
class SimilarIncidentAdmin(admin.ModelAdmin):
    list_display = ['incident', 'similar_to', 'similarity_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['incident__title', 'similar_to__title']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'incident', 'read', 'created_at']
    list_filter = ['notification_type', 'read', 'created_at']
    search_fields = ['message', 'user__username']
