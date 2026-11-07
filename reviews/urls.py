"""Adresses des pages de publication."""

from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('billets/nouveau/', views.ticket_create, name='ticket_create'),
]
