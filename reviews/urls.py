"""Adresses des pages de publication."""

from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('billets/nouveau/', views.ticket_form, name='ticket_create'),
    path('billets/<int:pk>/modifier/', views.ticket_form, name='ticket_edit'),
    path('billets/<int:pk>/supprimer/', views.ticket_delete, name='ticket_delete'),
    path('billets/<int:ticket_pk>/critique/', views.review_create, name='review_create'),
]
