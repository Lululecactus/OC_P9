"""Formulaires de publication des lecteurs."""

from django import forms

from .models import Review, Ticket


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


class ReviewForm(forms.ModelForm):
    """Prépare et valide la critique d’un lecteur."""

    class Meta:
        model = Review
        fields = ('headline', 'rating', 'body')
        labels = {
            'headline': 'Titre de la critique',
            'rating': 'Note sur 5',
            'body': 'Commentaire (facultatif)',
        }
        widgets = {
            # Un bouton par note ; range(6) fournit les entiers de 0 à 5.
            'rating': forms.RadioSelect(choices=[(note, str(note)) for note in range(6)]),
        }
