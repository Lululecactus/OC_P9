from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """Déclare l’application consacrée aux publications des lecteurs."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'
