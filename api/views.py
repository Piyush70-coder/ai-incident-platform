from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from incidents.models import Incident, IncidentComment, IncidentLog
from .serializers import IncidentSerializer, IncidentCommentSerializer, IncidentLogSerializer


class IncidentViewSet(viewsets.ModelViewSet):
    """API ViewSet for incidents"""
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return Incident.objects.none()
        return Incident.objects.filter(company=company)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to an incident"""
        incident = self.get_object()
        serializer = IncidentCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(incident=incident, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for an incident"""
        incident = self.get_object()
        logs = incident.logs.all()
        serializer = IncidentLogSerializer(logs, many=True)
        return Response(serializer.data)
