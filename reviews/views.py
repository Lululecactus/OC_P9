"""Pages de publication des lecteurs."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TicketForm
from .models import Ticket


@login_required
def ticket_form(request, pk=None):
    """Crée une demande ou modifie celle du lecteur connecté."""
    if pk is None:
        ticket = Ticket(user=request.user)
    else:
        ticket = get_object_or_404(Ticket, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            form.save()
            if pk is None:
                messages.success(request, 'Votre demande de critique a été publiée.')
            else:
                messages.success(request, 'Votre demande de critique a été modifiée.')
            return redirect('accounts:home')
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'reviews/ticket_form.html', {'form': form})
