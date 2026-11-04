"""Vérifications du parcours de connexion des lecteurs."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class LoginTests(TestCase):
    """Vérifie la connexion et la protection de la page d’accueil."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='lectrice', password='MotDePasse-Test-742!',
        )

    def test_login_displays_form(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_valid_credentials_open_home(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'lectrice', 'password': 'MotDePasse-Test-742!',
        })
        self.assertRedirects(response, reverse('accounts:home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertContains(
            self.client.get(reverse('accounts:home')), 'lectrice',
        )

    def test_invalid_password_displays_error(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'lectrice', 'password': 'incorrect',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_anonymous_visitor_is_redirected_to_login(self):
        response = self.client.get(reverse('accounts:home'))
        self.assertRedirects(response, '/connexion/?next=/accueil/')

    def test_external_redirect_is_rejected(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'lectrice',
            'password': 'MotDePasse-Test-742!',
            'next': 'https://example.com/',
        })
        self.assertRedirects(response, reverse('accounts:home'))

    def test_login_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('accounts:login'), {
            'username': 'lectrice', 'password': 'MotDePasse-Test-742!',
        })
        self.assertEqual(response.status_code, 403)


class LogoutTests(TestCase):
    """Vérifie la fermeture de session et la protection de la déconnexion."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='lecteur')

    def test_logout_with_csrf_closes_session_and_protects_home(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.get(reverse('accounts:home'))
        self.assertContains(response, 'Se déconnecter')
        token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('accounts:logout'), {'csrfmiddlewaretoken': token},
        )
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', client.session)
        self.assertRedirects(
            client.get(reverse('accounts:home')),
            '/connexion/?next=/accueil/',
        )

    def test_get_does_not_log_user_out(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_post_without_csrf_does_not_log_user_out(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 403)
        self.assertIn('_auth_user_id', client.session)
