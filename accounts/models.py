"""Définition du modèle utilisateur de LITRevu."""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Utilisateur de LITRevu"""

    pass