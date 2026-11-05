"""Gestion des publications et des abonnements dans l’administration Django."""

from django.contrib import admin

from .models import Review, Ticket, UserFollows


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Affiche les informations utiles pour retrouver un billet."""

    list_display = ('title', 'user', 'time_created')
    search_fields = ('title', 'user__username')
    readonly_fields = ('time_created',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Permet de retrouver une critique, sa note et le billet associé."""

    list_display = ('headline', 'ticket', 'user', 'rating', 'time_created')
    search_fields = ('headline', 'ticket__title', 'user__username')
    readonly_fields = ('time_created',)


@admin.register(UserFollows)
class UserFollowsAdmin(admin.ModelAdmin):
    """Affiche qui suit qui et permet de rechercher les deux lecteurs."""

    list_display = ('user', 'followed_user')
    search_fields = ('user__username', 'followed_user__username')
