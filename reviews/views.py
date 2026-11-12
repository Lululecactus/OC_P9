"""Pages de publication des lecteurs."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ReviewForm, TicketForm
from .models import Review, Ticket


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


@login_required
@require_http_methods(['GET', 'POST'])
def ticket_delete(request, pk):
    """Affiche la confirmation, puis supprime le billet de son auteur sur POST."""
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Votre demande de critique a été supprimée.')
        return redirect('accounts:home')
    return render(request, 'reviews/ticket_confirm_delete.html', {'ticket': ticket})


@login_required
@require_http_methods(['GET', 'POST'])
def review_create(request, ticket_pk):
    """Publie une critique en réponse au billet ouvert par le lecteur."""
    ticket = get_object_or_404(Ticket.visible_to(request.user), pk=ticket_pk)
    if request.method == 'POST':
        review = Review(ticket=ticket, user=request.user)
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre critique a été publiée.')
            return redirect('accounts:home')
    else:
        form = ReviewForm()
    return render(request, 'reviews/review_form.html', {'ticket': ticket, 'form': form})
