from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class LogoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

    def test_logout_get_request(self):
        """GET request to logout should fail with 405 (Method Not Allowed)"""
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_request(self):
        """POST request to logout should succeed and redirect"""
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        # Should redirect to login page as per settings.LOGOUT_REDIRECT_URL
        self.assertRedirects(response, '/accounts/login/', fetch_redirect_response=False)
