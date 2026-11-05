"""Modèles des publications des lecteurs."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
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


class Review(models.Model):
    """Avis d’un lecteur en réponse à un billet, avec une note sur cinq."""

    # Plusieurs critiques peuvent répondre au même billet.
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    headline = models.CharField(max_length=128)
    body = models.TextField(max_length=8192, blank=True)
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Affiche le titre de la critique plutôt qu’un numéro d’objet."""
        return self.headline
