"""Adresses des pages de publication."""

from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('billets/nouveau/', views.ticket_form, name='ticket_create'),
    path('billets/<int:pk>/modifier/', views.ticket_form, name='ticket_edit'),
]
