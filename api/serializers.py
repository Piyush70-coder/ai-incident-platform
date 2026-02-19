from rest_framework import serializers
from incidents.models import Incident, IncidentComment, IncidentLog, IncidentAnalysis


class IncidentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentLog
        fields = ['id', 'file_name', 'file_size', 'file_type', 'uploaded_at', 'processed']


class IncidentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentAnalysis
        fields = ['timeline', 'root_cause', 'explanation', 'mitigation_steps', 'confidence_score', 'category', 'analyzed_at']


class IncidentSerializer(serializers.ModelSerializer):
    logs = IncidentLogSerializer(many=True, read_only=True)
    analysis = IncidentAnalysisSerializer(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'severity', 'status', 'category',
            'affected_services', 'created_by_username', 'assigned_to_username',
            'created_at', 'updated_at', 'resolved_at', 'closed_at',
            'logs', 'analysis'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolved_at', 'closed_at']


class IncidentCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = IncidentComment
        fields = ['id', 'comment', 'user_username', 'created_at', 'attachments']
        read_only_fields = ['created_at']

