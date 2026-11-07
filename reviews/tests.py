"""Vérifications des premiers billets, dans une base de test séparée."""

from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Review, Ticket, UserFollows


class TicketCreateTests(TestCase):
    """Vérifie la publication depuis l’espace lecteur."""

    def test_anonymous_post_requires_login(self):
        url = reverse('reviews:ticket_create')
        response = self.client.post(url, {'title': 'Une demande'})
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")
        self.assertFalse(Ticket.objects.exists())

    def test_invalid_title_redisplays_form_without_saving(self):
        reader = get_user_model().objects.create_user(username='alice')
        self.client.force_login(reader)
        url = reverse('reviews:ticket_create')
        self.assertContains(self.client.get(url), 'multipart/form-data')
        response = self.client.post(url, {'description': 'Mon passage préféré'})
        self.assertContains(response, 'Mon passage préféré')
        self.assertIn('title', response.context['form'].errors)
        self.assertFalse(Ticket.objects.exists())

    def test_uploaded_image_and_author_come_from_authenticated_request(self):
        reader = get_user_model().objects.create_user(username='alice')
        other = get_user_model().objects.create_user(username='bob')
        self.client.force_login(reader)
        data = BytesIO()
        Image.new('RGB', (2, 2)).save(data, format='PNG')
        image = SimpleUploadedFile('couverture.png', data.getvalue(), content_type='image/png')
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post(reverse('reviews:ticket_create'), {
                'title': 'Dune', 'user': other.pk, 'image': image,
            }, follow=True)
            self.assertRedirects(response, reverse('accounts:home'))
            self.assertContains(response, 'Votre demande de critique a été publiée.')
            ticket = Ticket.objects.get()
            self.assertEqual(ticket.user, reader)
            self.assertTrue(ticket.image.storage.exists(ticket.image.name))


class TicketEditTests(TestCase):
    """Seul l’auteur peut ouvrir le billet et enregistrer sa correction."""

    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username='alice')
        cls.other = get_user_model().objects.create_user(username='bob')
        cls.ticket = Ticket.objects.create(title='Dune', user=cls.author)
        cls.url = reverse('reviews:ticket_edit', args=[cls.ticket.pk])

    def test_author_edits_existing_ticket_from_home(self):
        self.client.force_login(self.author)
        self.assertContains(self.client.get(reverse('accounts:home')), self.url)
        self.assertContains(self.client.get(self.url), 'value="Dune"')
        response = self.client.post(self.url, {'title': 'Le Messie de Dune', 'user': self.other.pk})
        self.assertRedirects(response, reverse('accounts:home'))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, 'Le Messie de Dune')
        self.assertEqual(self.ticket.user, self.author)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_other_reader_cannot_view_or_update_ticket(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse('accounts:home')), self.url)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {'title': 'Autre titre'}).status_code, 404)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, 'Dune')


class TicketTests(TestCase):
    """Vérifie la création d’un billet et son lien avec son auteur."""

    @classmethod
    def setUpTestData(cls):
        """Prépare un auteur sans utiliser les comptes de la base locale."""
        cls.user = get_user_model().objects.create_user(username='lectrice')

    def test_ticket_can_be_created_without_description_or_image(self):
        ticket = Ticket(title='Un avis sur ce livre ?', user=self.user)
        ticket.full_clean()
        ticket.save()
        ticket.refresh_from_db()
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.description, '')
        self.assertFalse(ticket.image)
        self.assertIsNotNone(ticket.time_created)
        self.assertEqual(str(ticket), 'Un avis sur ce livre ?')

    def test_validation_rejects_text_exceeding_specification_limits(self):
        ticket = Ticket(title='a' * 129, description='b' * 2049, user=self.user)
        # save() ne lance pas full_clean() : on vérifie explicitement la validation.
        with self.assertRaises(ValidationError) as error:
            ticket.full_clean()
        self.assertIn('title', error.exception.message_dict)
        # Pour TextField, max_length est vérifié par le champ de formulaire.
        description_field = Ticket._meta.get_field('description').formfield()
        with self.assertRaises(ValidationError):
            description_field.clean(ticket.description)

    def test_deleting_author_deletes_their_ticket(self):
        ticket = Ticket.objects.create(title='Une demande', user=self.user)
        self.user.delete()
        self.assertFalse(Ticket.objects.filter(pk=ticket.pk).exists())


class ReviewTests(TestCase):
    """Vérifie la note et les relations entre une critique, son auteur et son billet."""

    @classmethod
    def setUpTestData(cls):
        """Prépare un billet et une autre personne pour y répondre."""
        cls.author = get_user_model().objects.create_user(username='auteur_billet')
        cls.reviewer = get_user_model().objects.create_user(username='critique_lecteur')
        cls.ticket = Ticket.objects.create(title='Un livre à découvrir', user=cls.author)

    def test_review_accepts_both_rating_limits_and_optional_body(self):
        for rating in (0, 5):
            with self.subTest(rating=rating):
                review = Review(
                    ticket=self.ticket, user=self.reviewer,
                    rating=rating, headline='Mon avis',
                )
                review.full_clean()
                review.save()
                review.refresh_from_db()
                self.assertEqual(review.ticket, self.ticket)
                self.assertEqual(review.user, self.reviewer)
                self.assertEqual(review.body, '')
                self.assertIsNotNone(review.time_created)

    def test_validation_rejects_rating_outside_zero_to_five(self):
        for rating in (-1, 6):
            with self.subTest(rating=rating):
                review = Review(
                    ticket=self.ticket, user=self.reviewer,
                    rating=rating, headline='Mon avis',
                )
                with self.assertRaises(ValidationError) as error:
                    review.full_clean()
                self.assertIn('rating', error.exception.message_dict)

    def test_deleting_ticket_deletes_review_but_keeps_its_author(self):
        review = Review.objects.create(
            ticket=self.ticket, user=self.reviewer, rating=4, headline='Mon avis',
        )
        self.ticket.delete()
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=self.reviewer.pk).exists())


class UserFollowsTests(TestCase):
    """Vérifie le sens des abonnements et l’absence de doublons."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = get_user_model().objects.create_user(username='alice')
        cls.bob = get_user_model().objects.create_user(username='bob')

    def test_follow_is_directional_and_reverse_follow_is_allowed(self):
        follow = UserFollows.objects.create(user=self.alice, followed_user=self.bob)
        # Ces relations renvoient des abonnements, pas directement des utilisateurs.
        self.assertEqual(self.alice.following.get(), follow)
        self.assertEqual(self.bob.followed_by.get(), follow)
        self.assertFalse(self.bob.following.exists())
        UserFollows.objects.create(user=self.bob, followed_user=self.alice)
        self.assertEqual(UserFollows.objects.count(), 2)

    def test_database_rejects_duplicate_follow(self):
        UserFollows.objects.create(user=self.alice, followed_user=self.bob)
        # Le bloc transactionnel isole l’erreur attendue pendant ce test.
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserFollows.objects.create(user=self.alice, followed_user=self.bob)

    def test_deleting_user_removes_both_incoming_and_outgoing_follows(self):
        UserFollows.objects.create(user=self.alice, followed_user=self.bob)
        UserFollows.objects.create(user=self.bob, followed_user=self.alice)
        self.alice.delete()
        self.assertFalse(UserFollows.objects.exists())
        self.assertTrue(get_user_model().objects.filter(pk=self.bob.pk).exists())


class TicketAdminTests(TestCase):
    """Vérifie l’ajout d’un billet illustré et les droits d’accès à l’admin."""

    def test_superuser_can_create_ticket_with_image(self):
        user = get_user_model().objects.create_superuser(username='admin_test')
        self.client.force_login(user)
        self.assertEqual(
            self.client.get(reverse('admin:reviews_ticket_add')).status_code, 200,
        )
        image_data = BytesIO()
        Image.new('RGB', (2, 2), color='white').save(image_data, format='PNG')
        upload = SimpleUploadedFile(
            'livre.png', image_data.getvalue(), content_type='image/png',
        )
        # L’image du test ne doit pas rester dans le dossier media du projet.
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post(reverse('admin:reviews_ticket_add'), {
                'title': 'Une demande illustrée',
                'description': '',
                'user': user.pk,
                'image': upload,
                '_save': 'Enregistrer',
            })
            self.assertRedirects(response, reverse('admin:reviews_ticket_changelist'))
            ticket = Ticket.objects.get(title='Une demande illustrée')
            self.assertEqual(ticket.user, user)
            self.assertTrue(ticket.image.name.startswith('tickets/'))
            self.assertTrue(ticket.image.storage.exists(ticket.image.name))
            self.assertTrue(ticket.image.url.startswith('/media/tickets/'))

    def test_reader_cannot_add_ticket_through_admin(self):
        user = get_user_model().objects.create_user(username='lecteur_test')
        self.client.force_login(user)
        response = self.client.post(reverse('admin:reviews_ticket_add'), {
            'title': 'Billet refusé', 'user': user.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('admin:login')))
        self.assertFalse(Ticket.objects.exists())
