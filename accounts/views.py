"""Vues des pages de gestion des comptes."""

from django.shortcuts import render


def login_page(request):
    """Affiche la page de connexion, sans authentification pour le moment."""
    return render(request, 'accounts/login.html')
