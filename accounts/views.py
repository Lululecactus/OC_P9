"""Vues des pages de gestion des comptes."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    """Affiche un accueil réservé aux utilisateurs connectés."""
    return render(request, 'accounts/home.html')
