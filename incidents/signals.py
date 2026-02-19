from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Incident

@receiver(post_save, sender=Incident)
@receiver(post_delete, sender=Incident)
def invalidate_dashboard_cache(sender, instance, **kwargs):
    """
    Invalidate dashboard metrics cache when an incident is created, updated, or deleted.
    """
    if instance.company:
        cache_key = f'dashboard_metrics_{instance.company.id}'
        cache.delete(cache_key)
