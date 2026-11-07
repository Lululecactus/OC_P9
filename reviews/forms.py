"""Formulaires de publication des lecteurs."""

from django import forms

from .models import Ticket


class TicketForm(forms.ModelForm):
    """Prépare et valide la saisie d’une demande de critique."""

    class Meta:
        model = Ticket
        # L’auteur sera déterminé par la session du lecteur connecté.
        fields = ('title', 'description', 'image')
        labels = {
            'title': 'Titre',
            'description': 'Description (facultative)',
            'image': 'Image (facultative)',
        }
