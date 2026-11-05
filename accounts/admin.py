"""Configuration des utilisateurs dans l’administration Django."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


# UserAdmin fournit les écrans de gestion adaptés aux utilisateurs.
# On enregistre notre modèle pour le retrouver dans /admin/.
admin.site.register(User, UserAdmin)
