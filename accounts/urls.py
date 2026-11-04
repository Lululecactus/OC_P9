"""Adresses des pages de gestion des comptes."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views


app_name = 'accounts'

urlpatterns = [
    path(
        'connexion/',
        LoginView.as_view(template_name='accounts/login.html'),
        name='login',
    ),
    path('accueil/', views.home, name='home'),
    path('deconnexion/', LogoutView.as_view(), name='logout'),
]
