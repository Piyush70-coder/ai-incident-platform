def notifications(request):
    """Context processor to add unread notification count to all templates"""
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(read=False).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}

