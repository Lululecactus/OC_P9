"""Adresses des pages de gestion des comptes."""

from django.urls import path

from . import views


app_name = 'accounts'

urlpatterns = [
    path('connexion/', views.login_page, name='login'),
]
