from typing import Optional
from django.contrib.auth import get_user_model
from ..models import Incident, Notification

User = get_user_model()


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(
        user: User,
        incident: Optional[Incident],
        message: str,
        notification_type: str
    ) -> Notification:
        """Create a new notification"""
        return Notification.objects.create(
            user=user,
            incident=incident,
            message=message,
            notification_type=notification_type
        )
    
    @staticmethod
    def notify_incident_created(incident: Incident):
        """Notify relevant users when an incident is created"""
        # Notify company admins
        admins = incident.company.users.filter(role__in=['company_admin', 'super_admin'])
        for admin in admins:
            NotificationService.create_notification(
                user=admin,
                incident=incident,
                message=f"New {incident.get_severity_display().lower()} incident: {incident.title}",
                notification_type='incident_created'
            )
    
    @staticmethod
    def notify_incident_assigned(incident: Incident, assigned_user: User):
        """Notify user when assigned to an incident"""
        NotificationService.create_notification(
            user=assigned_user,
            incident=incident,
            message=f"You have been assigned to incident: {incident.title}",
            notification_type='incident_assigned'
        )
    
    @staticmethod
    def notify_incident_updated(incident: Incident, user: User, change_description: str):
        """Notify relevant users when an incident is updated"""
        # Notify assigned user and creator
        users_to_notify = []
        if incident.assigned_to:
            users_to_notify.append(incident.assigned_to)
        if incident.created_by and incident.created_by != user:
            users_to_notify.append(incident.created_by)
        
        for notify_user in users_to_notify:
            if notify_user != user:  # Don't notify the user who made the change
                NotificationService.create_notification(
                    user=notify_user,
                    incident=incident,
                    message=f"Incident updated: {incident.title} - {change_description}",
                    notification_type='incident_updated'
                )
    
    @staticmethod
    def notify_status_changed(incident: Incident, user: User, from_status: str, to_status: str):
        """Notify when incident status changes"""
        users_to_notify = []
        if incident.assigned_to:
            users_to_notify.append(incident.assigned_to)
        if incident.created_by:
            users_to_notify.append(incident.created_by)
        
        for notify_user in set(users_to_notify):
            if notify_user != user:
                NotificationService.create_notification(
                    user=notify_user,
                    incident=incident,
                    message=f"Incident status changed: {incident.title} ({from_status} → {to_status})",
                    notification_type='status_changed'
                )
    
    @staticmethod
    def notify_comment_added(incident: Incident, comment_user: User):
        """Notify when a comment is added to an incident"""
        users_to_notify = []
        if incident.assigned_to:
            users_to_notify.append(incident.assigned_to)
        if incident.created_by:
            users_to_notify.append(incident.created_by)
        
        # Also notify other users who commented
        commenters = incident.comments.exclude(user=comment_user).values_list('user', flat=True).distinct()
        users_to_notify.extend([User.objects.get(pk=pk) for pk in commenters])
        
        for notify_user in set(users_to_notify):
            if notify_user != comment_user:
                NotificationService.create_notification(
                    user=notify_user,
                    incident=incident,
                    message=f"New comment on incident: {incident.title}",
                    notification_type='comment_added'
                )
    
    @staticmethod
    def cleanup_old_notifications(days: int = 30):
        """Delete notifications older than specified days"""
        from datetime import timedelta
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        Notification.objects.filter(created_at__lt=cutoff_date, read=True).delete()

