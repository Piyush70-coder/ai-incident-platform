import os
import django
import time
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from incidents.models import Incident
from companies.models import Company
from incidents.services.analytics import AnalyticsService

User = get_user_model()

def verify_real_time_updates():
    print("--- Verifying Real-Time Updates ---")
    
    # Setup
    user = User.objects.first()
    if not user:
        print("No user found, creating one")
        user = User.objects.create_user(username='testadmin', password='password')
    
    company = Company.objects.first()
    if not company:
        print("No company found, creating one")
        company = Company.objects.create(name="Test Corp", owner=user)
    
    # Clear cache initially
    cache_key = f'dashboard_metrics_{company.id}'
    cache.delete(cache_key)
    
    # 1. Get initial metrics
    analytics = AnalyticsService()
    metrics_1 = analytics.get_dashboard_metrics(company)
    initial_resolved = metrics_1['resolved_incidents']
    print(f"Initial Resolved: {initial_resolved}")
    
    # 2. Create and Resolve an Incident
    print("Creating and resolving a new incident...")
    incident = Incident.objects.create(
        title="Test Realtime Update",
        description="Testing cache invalidation",
        company=company,
        created_by=user,
        severity="medium"
    )
    
    # Simulate resolving
    incident.status = 'resolved'
    incident.resolved_at = timezone.now()
    incident.save()
    
    # 3. Check metrics again (should be updated immediately due to signal)
    metrics_2 = analytics.get_dashboard_metrics(company)
    new_resolved = metrics_2['resolved_incidents']
    print(f"New Resolved: {new_resolved}")
    
    if new_resolved == initial_resolved + 1:
        print("✅ SUCCESS: Dashboard updated immediately!")
    else:
        print("❌ FAILURE: Dashboard did not update. Cache might be stale.")
        print(f"Expected {initial_resolved + 1}, got {new_resolved}")
        
    # Cleanup
    incident.delete()
    print("Test incident deleted.")

if __name__ == "__main__":
    verify_real_time_updates()
