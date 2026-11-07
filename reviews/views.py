"""Pages de publication des lecteurs."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import TicketForm


@login_required
def ticket_create(request):
    """Affiche la demande de critique et l’enregistre au nom du lecteur."""
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            # On complète le billet avec son auteur avant de l’écrire en base.
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, 'Votre demande de critique a été publiée.')
            return redirect('accounts:home')
    else:
        form = TicketForm()
    return render(request, 'reviews/ticket_create.html', {'form': form})
