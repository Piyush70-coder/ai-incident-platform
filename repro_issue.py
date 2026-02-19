import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from companies.models import Company
from incidents.models import Incident
from incidents.views import past_incidents_view, incident_detail_view
from django.http import Http404

User = get_user_model()

def reproduce_issue():
    # 1. Clean up (optional, but good for reproducibility if db is persistent)
    # Ideally we use a test db, but here we might be using the main db.
    # To avoid messing up main db, we should be careful or use transaction.atomic and rollback.
    # For now, I'll just create unique names.
    
    unique_suffix = "repro_" + os.urandom(4).hex()
    
    # 2. Create Companies
    c1 = Company.objects.create(name=f"Company 1 {unique_suffix}")
    c2 = Company.objects.create(name=f"Company 2 {unique_suffix}")
    
    # 3. Create User linked to C1
    u1 = User.objects.create_user(username=f"user1_{unique_suffix}", password="password")
    u1.company = c1
    u1.save()
    
    # 4. Create Incident linked to C2 (Resolved)
    i2 = Incident.objects.create(
        title=f"Incident C2 {unique_suffix}",
        description="Description",
        company=c2,
        status="resolved",
        severity="low"
    )
    
    # 5. Simulate request to past_incidents_view as U1
    factory = RequestFactory()
    request = factory.get('/incidents/past/')
    request.user = u1
    request.company = c1 # Middleware would set this
    
    print("--- Testing past_incidents_view ---")
    response = past_incidents_view(request)
    
    # Check if i2 is in the response context
    # Since it's a rendered response, we might need to inspect the context if available,
    # or the content. But RequestFactory responses don't always have context if using render().
    # render() returns HttpResponse, not TemplateResponse usually, unless configured.
    # However, we can check the content for the incident title.
    
    content = response.content.decode('utf-8')
    if i2.title in content:
        print(f"BUG STILL PRESENT: User from {c1.name} can see incident from {c2.name}")
    else:
        print("FIX VERIFIED: User cannot see incident from another company.")

    # 6. Simulate request to incident_detail_view as U1 for I2
    print("\n--- Testing incident_detail_view ---")
    request_detail = factory.get(f'/incidents/{i2.id}/')
    request_detail.user = u1
    request_detail.company = c1
    
    try:
        incident_detail_view(request_detail, i2.id)
        print("Access GRANTED to detail view (Unexpected if view enforces company)")
    except Http404:
        print("Access DENIED to detail view (Correct behavior for detail view)")
    except Exception as e:
        print(f"Other error: {e}")

    # Cleanup
    i2.delete()
    u1.delete()
    c1.delete()
    c2.delete()

if __name__ == "__main__":
    reproduce_issue()
