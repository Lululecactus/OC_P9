"""Formulaires de publication des lecteurs."""

from django import forms
from django.contrib.auth import get_user_model

from .models import Review, Ticket
from .image_fields import CoverImageField


class FollowForm(forms.Form):
    """Recherche un lecteur par son nom exact et vérifie l’abonnement."""

    username = forms.CharField(label='Nom d’utilisateur', max_length=150)

    def __init__(self, *args, reader, **kwargs):
        super().__init__(*args, **kwargs)
        self.reader = reader

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            self.followed_user = get_user_model().objects.get(username=username, is_active=True)
        except get_user_model().DoesNotExist:
            raise forms.ValidationError('Aucun lecteur actif ne porte ce nom.')
        if self.followed_user == self.reader:
            raise forms.ValidationError('Vous ne pouvez pas vous suivre vous-même.')
        if self.reader.following.filter(followed_user=self.followed_user).exists():
            raise forms.ValidationError('Vous suivez déjà ce lecteur.')
        return username


class TicketForm(forms.ModelForm):
    """Prépare et valide la saisie d’une demande de critique."""

    image = CoverImageField(
        required=False, label='Image (facultative)',
        help_text='PNG, JPEG ou WebP — 5 Mo et 12 millions de pixels maximum.',
    )

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
