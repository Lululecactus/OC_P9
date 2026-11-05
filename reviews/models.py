"""Modèles des publications des lecteurs."""

from django.conf import settings
from django.db import models


class Ticket(models.Model):
    """Demande de critique publiée par un utilisateur sur un livre ou un article."""

    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048, blank=True)
    # On référence notre modèle utilisateur via les réglages du projet.
    # CASCADE supprime les billets si leur auteur est supprimé.
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    # Le fichier sera stocké séparément ; la base conserve son chemin.
    image = models.ImageField(upload_to='tickets/', null=True, blank=True)
    # Django renseigne cette date lors du premier enregistrement.
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Représente le billet par son titre, notamment dans l’administration."""
        return self.title
