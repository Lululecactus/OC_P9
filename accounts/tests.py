"""Vérifications des formulaires et de l’authentification des lecteurs."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .forms import SignupForm


# TestCase travaille dans une base de test, distincte de la base du projet.
class SignupFormTests(TestCase):
    """Vérifie l’inscription avec notre modèle utilisateur personnalisé."""

    def signup_data(self, **changes):
        """Prépare une saisie valide que chaque test peut modifier."""
        data = {
            'username': 'nouvelle_lectrice',
            'password1': 'Lecture-Test-742!',
            'password2': 'Lecture-Test-742!',
        }
        data.update(changes)
        return data

    def test_valid_form_creates_reader_with_hashed_password(self):
        form = SignupForm(data=self.signup_data())
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()
        user.refresh_from_db()

        self.assertIsInstance(user, get_user_model())
        self.assertEqual(user.username, 'nouvelle_lectrice')
        self.assertNotEqual(user.password, 'Lecture-Test-742!')
        self.assertTrue(user.check_password('Lecture-Test-742!'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_different_passwords_are_rejected(self):
        form = SignupForm(data=self.signup_data(password2='Autre-Test-845!'))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_existing_username_is_rejected_even_with_different_case(self):
        get_user_model().objects.create_user(username='Nouvelle_Lectrice')
        form = SignupForm(data=self.signup_data())
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_password_uses_project_validators(self):
        form = SignupForm(data=self.signup_data(password1='123', password2='123'))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertEqual(get_user_model().objects.count(), 0)


class SignupViewTests(TestCase):
    """Vérifie le parcours d’inscription via les requêtes HTTP."""

    def test_signup_displays_book_and_masked_password_fields(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/base.html')
        self.assertContains(response, 'type="password"', count=2)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, 'Conseils pour le mot de passe')
        self.assertNotContains(response, '150 caractères maximum')
        self.assertContains(response, 'Vos lectures ont')

    def test_signup_creates_reader_then_returns_to_login(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'nouveau',
            'password1': 'Lecture-Test-742!',
            'password2': 'Lecture-Test-742!',
            'is_staff': 'true',
            'is_superuser': 'true',
        }, follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertContains(response, 'Votre compte est créé.')
        user = get_user_model().objects.get(username='nouveau')
        self.assertTrue(user.check_password('Lecture-Test-742!'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotIn('_auth_user_id', self.client.session)
        response = self.client.post(reverse('accounts:login'), {
            'username': 'nouveau', 'password': 'Lecture-Test-742!',
        })
        self.assertRedirects(response, reverse('accounts:home'))

    def test_invalid_signup_keeps_errors_and_does_not_create_user(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'nouveau',
            'password1': 'Lecture-Test-742!',
            'password2': 'Autre-Test-845!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('password2', response.context['form'].errors)
        self.assertContains(response, 'id="id_password2_error"')
        self.assertNotContains(response, 'Lecture-Test-742!')
        self.assertFalse(get_user_model().objects.exists())

    def test_signup_rejects_missing_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('accounts:signup'), {
            'username': 'nouveau',
            'password1': 'Lecture-Test-742!',
            'password2': 'Lecture-Test-742!',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(get_user_model().objects.exists())


class EntryTests(TestCase):
    """L’adresse principale ouvre toujours la connexion."""

    def test_visitor_starts_at_login(self):
        self.assertRedirects(self.client.get('/'), reverse('accounts:login'))

    def test_root_keeps_login_as_default_for_a_reader(self):
        user = get_user_model().objects.create_user(username='lecteur')
        self.client.force_login(user)
        self.assertRedirects(self.client.get('/'), reverse('accounts:login'))


class LoginTests(TestCase):
    """Vérifie la connexion et la protection de la page d’accueil."""

    @classmethod
    def setUpTestData(cls):
        """Prépare le compte commun aux tests de cette classe."""
        cls.user = get_user_model().objects.create_user(
            username='lectrice', password='MotDePasse-Test-742!',
        )

    def test_login_displays_form(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, reverse('accounts:signup'))

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

    def test_inactive_account_cannot_log_in(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        response = self.client.post(reverse('accounts:login'), {
            'username': 'lectrice', 'password': 'MotDePasse-Test-742!',
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
        """Prépare le compte commun aux tests de cette classe."""
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


class AdminAccessTests(TestCase):
    """L’administration expose notre modèle seulement aux comptes autorisés."""

    def test_anonymous_visitor_must_log_in(self):
        response = self.client.get(reverse('admin:accounts_user_changelist'))
        self.assertRedirects(response, '/admin/login/?next=/admin/accounts/user/')

    def test_ordinary_reader_cannot_access_user_list(self):
        user = get_user_model().objects.create_user(username='lecteur_admin_test')
        self.client.force_login(user)
        response = self.client.get(reverse('admin:accounts_user_changelist'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('admin:login')))

    def test_superuser_can_view_custom_users_and_edit_form(self):
        user = get_user_model().objects.create_superuser(
            username='admin_test', password='Admin-Test-742!',
        )
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
        response = self.client.get(reverse('admin:accounts_user_changelist'))
        self.assertContains(response, 'admin_test')
        response = self.client.get(reverse('admin:accounts_user_change', args=[user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
