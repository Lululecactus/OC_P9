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
