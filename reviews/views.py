"""Pages de publication des lecteurs."""

from PIL import Image, UnidentifiedImageError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe
from django.views.decorators.cache import never_cache

from .forms import FollowForm, ReviewForm, TicketForm
from .models import Review, Ticket, UserFollows


@login_required
@require_safe
@never_cache
def ticket_image(request, path):
    """Protège les images avec les mêmes droits de lecture que les publications."""
    visible_tickets = Ticket.visible_to(request.user).values('pk')
    reviewed_tickets = Review.visible_to(request.user).values('ticket_id')
    ticket = get_object_or_404(
        Ticket.objects.filter(Q(pk__in=visible_tickets) | Q(pk__in=reviewed_tickets)),
        image=path,
    )
    try:
        stream = ticket.image.open('rb')
    except (FileNotFoundError, OSError):
        raise Http404
    try:
        # Ne jamais déduire le type HTTP du nom fourni lors d’un ancien envoi.
        image = Image.open(stream, formats=['PNG', 'JPEG', 'WEBP'])
        content_type = Image.MIME[image.format]
        stream.seek(0)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        stream.close()
        raise Http404
    response = FileResponse(stream, content_type=content_type)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response


@login_required
@require_http_methods(['GET', 'POST'])
def subscriptions(request):
    """Affiche les relations du lecteur et permet de suivre un autre compte."""
    form = FollowForm(request.POST if request.method == 'POST' else None, reader=request.user)
    if request.method == 'POST' and form.is_valid():
        # La contrainte unique et get_or_create protègent aussi les envois simultanés.
        UserFollows.objects.get_or_create(user=request.user, followed_user=form.followed_user)
        messages.success(request, f'Vous suivez désormais {form.followed_user.username}.')
        return redirect('reviews:subscriptions')
    return render(request, 'reviews/subscriptions.html', {
        'form': form,
        'following': request.user.following.select_related('followed_user').order_by('followed_user__username'),
        'followers': request.user.followed_by.select_related('user').order_by('user__username'),
    })


@login_required
@require_POST
def unfollow(request, pk):
    """Supprime uniquement un abonnement appartenant au lecteur connecté."""
    follow = get_object_or_404(UserFollows, pk=pk, user=request.user)
    username = follow.followed_user.username
    follow.delete()
    messages.success(request, f'Vous ne suivez plus {username}.')
    return redirect('reviews:subscriptions')


@login_required
@require_http_methods(['GET', 'POST'])
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
def review_create_with_ticket(request):
    """Publie un nouveau billet et sa critique depuis un seul formulaire."""
    if request.method == 'POST':
        ticket_form = TicketForm(request.POST, request.FILES, instance=Ticket(user=request.user))
        review_form = ReviewForm(request.POST, instance=Review(user=request.user))
        # Valider les deux formulaires pour afficher toutes les erreurs à la fois.
        ticket_valid = ticket_form.is_valid()
        review_valid = review_form.is_valid()
        if ticket_valid and review_valid:
            with transaction.atomic():
                ticket = ticket_form.save()
                review = review_form.save(commit=False)
                review.ticket = ticket
                review.save()
            messages.success(request, 'Votre critique a été publiée.')
            return redirect('accounts:home')
    else:
        ticket_form = TicketForm()
        review_form = ReviewForm()
    return render(request, 'reviews/review_create_with_ticket.html', {
        'ticket_form': ticket_form, 'review_form': review_form,
    })


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


@login_required
@require_http_methods(['GET', 'POST'])
def review_edit(request, pk):
    """Permet à l’auteur de corriger sa critique, même après un désabonnement."""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre critique a été modifiée.')
            return redirect('accounts:home')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'reviews/review_form.html', {
        'ticket': review.ticket, 'form': form,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def review_delete(request, pk):
    """Confirme puis supprime uniquement la critique du lecteur connecté."""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Votre critique a été supprimée.')
        return redirect('accounts:home')
    return render(request, 'reviews/review_confirm_delete.html', {'review': review})
