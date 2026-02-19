import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from incidents.views import notifications_view
from incidents.models import Notification
from accounts.models import CustomUser

def verify_notifications_fix():
    # Get a user (or create one)
    user = CustomUser.objects.first()
    if not user:
        print("No user found, creating one...")
        user = CustomUser.objects.create(username='testuser', email='test@example.com')
        user.set_password('password')
        user.save()

    # Create a test notification
    notification = Notification.objects.create(
        user=user,
        message="Test Notification",
        notification_type="incident_created"
    )
    print(f"Created notification {notification.id}, read={notification.read}")

    # Setup RequestFactory
    factory = RequestFactory()

    # Test 1: Mark Read (Single)
    print("\nTesting 'Mark Read'...")
    request = factory.post('/notifications/', {
        'mark_read': '',
        'notification_id': str(notification.id)
    })
    request.user = user
    
    # Add messages support
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    response = notifications_view(request)
    
    # Check result
    notification.refresh_from_db()
    print(f"Notification read status after single mark: {notification.read}")
    if notification.read:
        print("✅ Single Mark Read: SUCCESS")
    else:
        print("❌ Single Mark Read: FAILED")

    # Reset
    notification.read = False
    notification.save()

    # Test 2: Mark All Read
    print("\nTesting 'Mark All Read'...")
    request = factory.post('/notifications/', {
        'mark_all_read': ''
    })
    request.user = user
    setattr(request, 'session', 'session')
    setattr(request, '_messages', messages)

    response = notifications_view(request)

    # Check result
    notification.refresh_from_db()
    print(f"Notification read status after mark all: {notification.read}")
    if notification.read:
        print("✅ Mark All Read: SUCCESS")
    else:
        print("❌ Mark All Read: FAILED")

if __name__ == "__main__":
    try:
        verify_notifications_fix()
    except Exception as e:
        print(f"Error: {e}")
