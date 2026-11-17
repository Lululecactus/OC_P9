"""Régressions de sécurité : données hostiles, CSRF et fichiers envoyés."""

from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from .forms import TicketForm
from .image_fields import CoverImageField
from .models import Review, Ticket, UserFollows


def image_upload(name='couverture.png', suffix=b''):
    data = BytesIO()
    Image.new('RGB', (2, 2)).save(data, format='PNG')
    return SimpleUploadedFile(name, data.getvalue() + suffix, content_type='image/png')


class PublicationSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username='auteur')
        cls.other = get_user_model().objects.create_user(username='autre')
        cls.ticket = Ticket.objects.create(title='Original', user=cls.author)
        cls.review = Review.objects.create(ticket=cls.ticket, user=cls.author, headline='Avis', rating=4)

    def setUp(self):
        self.client.force_login(self.author)

    def test_sql_payload_is_stored_as_text_without_modifying_other_records(self):
        payload = "'); DROP TABLE reviews_ticket; --"
        response = self.client.post(reverse('reviews:review_create_with_ticket'), {
            'title': payload, 'description': payload,
            'headline': payload, 'body': payload, 'rating': '4',
        })
        self.assertRedirects(response, reverse('accounts:home'))
        self.assertEqual(Ticket.objects.get(title=payload).description, payload)
        self.assertEqual(Review.objects.get(headline=payload).body, payload)
        self.assertTrue(Ticket.objects.filter(pk=self.ticket.pk, title='Original').exists())
        response = self.client.post(reverse('reviews:subscriptions'), {'username': "' OR 1=1 --"})
        self.assertIn('username', response.context['form'].errors)
        self.assertFalse(UserFollows.objects.exists())

    def test_stored_xss_is_escaped_in_feed_forms_and_confirmation_pages(self):
        payload = '\"><script>alert(1)</script><img src=x onerror=alert(2)>'
        self.client.post(reverse('reviews:ticket_edit', args=[self.ticket.pk]), {
            'title': payload, 'description': payload,
        })
        self.client.post(reverse('reviews:review_edit', args=[self.review.pk]), {
            'headline': payload, 'body': payload, 'rating': '4',
        })
        urls = [
            reverse('accounts:home'),
            reverse('reviews:ticket_edit', args=[self.ticket.pk]),
            reverse('reviews:ticket_delete', args=[self.ticket.pk]),
            reverse('reviews:review_create', args=[self.ticket.pk]),
            reverse('reviews:review_edit', args=[self.review.pk]),
            reverse('reviews:review_delete', args=[self.review.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, escape(payload))
                self.assertNotContains(response, '<script>alert(1)</script>')
                self.assertNotContains(response, '<img src=x')

    def test_all_publication_mutations_reject_missing_csrf_and_foreign_origin(self):
        follow = UserFollows.objects.create(user=self.author, followed_user=self.other)
        urls = [
            reverse('reviews:ticket_create'),
            reverse('reviews:ticket_edit', args=[self.ticket.pk]),
            reverse('reviews:ticket_delete', args=[self.ticket.pk]),
            reverse('reviews:review_create', args=[self.ticket.pk]),
            reverse('reviews:review_create_with_ticket'),
            reverse('reviews:review_edit', args=[self.review.pk]),
            reverse('reviews:review_delete', args=[self.review.pk]),
            reverse('reviews:subscriptions'),
            reverse('reviews:unfollow', args=[follow.pk]),
        ]
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.author)
        client.get(reverse('accounts:home'))
        token = client.cookies['csrftoken'].value
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(client.post(url).status_code, 403)
                response = client.post(url, {'csrfmiddlewaretoken': token}, HTTP_ORIGIN='https://hostile.example')
                self.assertEqual(response.status_code, 403)
        self.assertTrue(Ticket.objects.filter(pk=self.ticket.pk).exists())
        self.assertTrue(Review.objects.filter(pk=self.review.pk).exists())
        self.assertTrue(UserFollows.objects.filter(pk=follow.pk).exists())


class ImageSecurityTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.author = get_user_model().objects.create_user(username='auteur')
        self.other = get_user_model().objects.create_user(username='autre')
        self.client.force_login(self.author)

    def publish_image(self):
        response = self.client.post(reverse('reviews:ticket_create'), {
            'title': 'Couverture', 'image': image_upload(),
        })
        self.assertRedirects(response, reverse('accounts:home'))
        return Ticket.objects.get()

    def test_upload_is_reencoded_with_generated_name_and_no_appended_script(self):
        marker = b'<script>alert(1)</script>'
        form = TicketForm({'title': 'Livre'}, {'image': image_upload('hostile.png', marker)})
        self.assertTrue(form.is_valid(), form.errors)
        cleaned = form.cleaned_data['image']
        self.assertNotEqual(cleaned.name, 'hostile.png')
        self.assertTrue(cleaned.name.endswith('.png'))
        self.assertNotIn(marker, cleaned.read())
        cleaned.seek(0)
        with Image.open(cleaned) as image:
            self.assertEqual((image.format, image.size), ('PNG', (2, 2)))

    def test_fake_images_and_svg_are_rejected(self):
        for name, data in (
            ('fake.png', b'<script>alert(1)</script>'),
            ('image.svg', b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>'),
        ):
            with self.subTest(name=name):
                form = TicketForm({'title': 'Livre'}, {'image': SimpleUploadedFile(name, data)})
                self.assertFalse(form.is_valid())
                self.assertIn('image', form.errors)

    def test_size_and_pixel_limits_are_enforced(self):
        upload = SimpleUploadedFile('large.png', b'x' * (CoverImageField.max_bytes + 1))
        form = TicketForm({'title': 'Livre'}, {'image': upload})
        with patch('reviews.image_fields.Image.open') as decoder:
            self.assertFalse(form.is_valid())
            decoder.assert_not_called()
        with patch.object(CoverImageField, 'max_pixels', 3):
            form = TicketForm({'title': 'Livre'}, {'image': image_upload()})
            self.assertFalse(form.is_valid())
            self.assertIn('image', form.errors)

    def test_images_require_login_and_publication_visibility(self):
        ticket = self.publish_image()
        url = ticket.image.url
        self.client.logout()
        self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        follow = UserFollows.objects.create(user=self.other, followed_user=self.author)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('sandbox', response['Content-Security-Policy'])
        response.close()
        follow.delete()
        self.assertEqual(self.client.get(url).status_code, 404)
        # Une critique personnelle reste visible après un désabonnement, image comprise.
        Review.objects.create(ticket=ticket, user=self.other, headline='Mon avis', rating=3)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_missing_files_and_path_traversal_do_not_expose_local_files(self):
        ticket = self.publish_image()
        ticket.image.storage.delete(ticket.image.name)
        self.assertEqual(self.client.get(ticket.image.url).status_code, 404)
        for path in ('/media/../db.sqlite3', '/media/%2e%2e/.django-secret-key', '/media/inconnu.png'):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_legacy_image_type_does_not_depend_on_filename(self):
        # Ancien fichier ou import hors formulaire : ne jamais le servir en HTML.
        ticket = Ticket.objects.create(
            title='Ancien fichier', user=self.author,
            image=image_upload('ancien.html', b'<script>alert(1)</script>'),
        )
        response = self.client.get(ticket.image.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertIn('sandbox', response['Content-Security-Policy'])
        response.close()

    def test_edit_preserves_image_unless_explicitly_cleared(self):
        ticket = self.publish_image()
        name = ticket.image.name
        url = reverse('reviews:ticket_edit', args=[ticket.pk])
        self.assertRedirects(self.client.post(url, {'title': 'Titre corrigé'}), reverse('accounts:home'))
        ticket.refresh_from_db()
        self.assertEqual(ticket.image.name, name)
        self.client.post(url, {'title': 'Sans image', 'image-clear': 'on'})
        ticket.refresh_from_db()
        self.assertFalse(ticket.image)
        self.assertEqual(self.client.get('/media/' + name).status_code, 404)

    def test_admin_uses_the_same_upload_validation(self):
        admin = get_user_model().objects.create_superuser(username='admin')
        self.client.force_login(admin)
        response = self.client.post(reverse('admin:reviews_ticket_add'), {
            'title': 'Refusé', 'user': admin.pk,
            'image': SimpleUploadedFile('fake.png', b'<script>alert(1)</script>'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('image', response.context['adminform'].form.errors)
        self.assertFalse(Ticket.objects.exists())
