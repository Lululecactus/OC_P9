"""Gestion des billets depuis l’administration Django."""

from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Affiche les informations utiles pour retrouver un billet."""

    list_display = ('title', 'user', 'time_created')
    search_fields = ('title', 'user__username')
    readonly_fields = ('time_created',)
