"""Définition du modèle utilisateur de LITRevu."""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Utilisateur du site, basé sur le modèle fourni par Django.

    AbstractUser apporte déjà le nom d’utilisateur, le mot de passe et les droits.
    On garde notre propre classe pour pouvoir ajouter des champs plus tard.
    """

    # Aucun champ supplémentaire pour le moment.
    pass
