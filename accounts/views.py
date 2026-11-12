"""Vues des pages de gestion des comptes."""

from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from reviews.models import Review, Ticket

from .forms import SignupForm


def entry(request):
    """Ouvre le livre à la page de connexion, l’entrée par défaut du site."""
    return redirect('accounts:login')


def signup(request):
    """Affiche l’inscription et crée un lecteur si les données sont valides."""
    # POST correspond à l’envoi du formulaire par le navigateur.
    if request.method == 'POST':
        # On confie les données reçues au formulaire pour les vérifier.
        form = SignupForm(request.POST)
        # Django vérifie notamment le nom et les deux mots de passe.
        if form.is_valid():
            # UserCreationForm hache le mot de passe avant de sauvegarder.
            form.save()
            messages.success(request, 'Votre compte est créé. Vous pouvez vous connecter.')
            # Le compte existe, mais l’utilisateur doit encore se connecter.
            return redirect('accounts:login')
    else:
        # À l’ouverture de la page, on prépare un formulaire vide.
        form = SignupForm()
    # Si la saisie est invalide, le même formulaire contient aussi les erreurs.
    # Le dictionnaire rend la variable form disponible dans le template HTML.
    return render(request, 'accounts/signup.html', {'form': form})


# Ce décorateur renvoie vers la connexion si la personne n’a pas de session.
@login_required
def home(request):
    """Affiche un accueil réservé aux utilisateurs connectés."""
    tickets = Ticket.visible_to(request.user).select_related('user')
    reviews = Review.visible_to(request.user).select_related('user', 'ticket')
    # On trie les deux types de publication ensemble pour afficher la plus récente en premier.
    posts = sorted(chain(tickets, reviews), key=lambda post: (post.time_created, post.pk), reverse=True)
    return render(request, 'accounts/home.html', {'posts': posts})
