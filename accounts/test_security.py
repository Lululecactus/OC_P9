"""Tests ciblés des entrées hostiles et des en-têtes de sécurité."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape


class AccountSecurityTests(TestCase):
    def test_sql_payload_does_not_authenticate_or_create_a_user(self):
        get_user_model().objects.create_user(username='alice', password='Lecture-Test-742!')
        payload = "' OR 1=1 --"
        response = self.client.post(reverse('accounts:login'), {
            'username': payload, 'password': payload,
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.post(reverse('accounts:signup'), {
            'username': payload, 'password1': 'Lecture-Test-742!', 'password2': 'Lecture-Test-742!',
        })
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_reflected_xss_is_escaped_in_account_forms(self):
        payload = '\"><img src=x onerror=alert(1)>'
        for name in ('accounts:login', 'accounts:signup'):
            response = self.client.post(reverse(name), {'username': payload})
            self.assertContains(response, escape(payload))
            self.assertNotContains(response, '<img src=x')

    def test_untrusted_hosts_are_rejected_and_security_headers_are_present(self):
        response = self.client.get(reverse('accounts:login'), HTTP_HOST='hostile.example')
        self.assertEqual(response.status_code, 400)
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.cookies['csrftoken']['samesite'], 'Lax')

    def test_successful_login_uses_http_only_session_cookie(self):
        get_user_model().objects.create_user(username='alice', password='Lecture-Test-742!')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'alice', 'password': 'Lecture-Test-742!',
        })
        self.assertTrue(response.cookies['sessionid']['httponly'])
        self.assertEqual(response.cookies['sessionid']['samesite'], 'Lax')
