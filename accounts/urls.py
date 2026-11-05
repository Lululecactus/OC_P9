"""Adresses des pages de gestion des comptes."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views


# Cet espace de noms permet d’écrire accounts:login dans les templates.
app_name = 'accounts'

urlpatterns = [
    path('', views.entry, name='entry'),
    path('inscription/', views.signup, name='signup'),
    path(
        'connexion/',
        # Django fournit déjà la vérification des identifiants et la session.
        LoginView.as_view(template_name='accounts/login.html'),
        name='login',
    ),
    path('accueil/', views.home, name='home'),
    # LogoutView ferme la session lors d’un POST ; le formulaire fournit le jeton CSRF.
    path('deconnexion/', LogoutView.as_view(), name='logout'),
]
