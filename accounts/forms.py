"""Formulaires de gestion des comptes de LITRevu."""

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class SignupForm(UserCreationForm):
    """Crée un lecteur avec les validations de mot de passe de Django."""

    def __init__(self, *args, **kwargs):
        """Prépare les champs Django, puis allège les textes d’aide affichés."""
        # On laisse d’abord le formulaire parent construire ses champs.
        super().__init__(*args, **kwargs)
        # Les erreurs expliquent les saisies refusées ; le formulaire reste épuré.
        for field in self.fields.values():
            field.help_text = ''

    class Meta(UserCreationForm.Meta):
        """Indique le modèle et les champs utilisés pour créer le compte."""

        # Cette fonction retrouve le modèle indiqué par AUTH_USER_MODEL.
        model = get_user_model()
        # password1 et password2 sont déjà ajoutés par UserCreationForm.
        fields = ('username',)
