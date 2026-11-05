"""Vérifications des premiers billets, dans une base de test séparée."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Ticket


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
