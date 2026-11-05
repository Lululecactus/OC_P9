from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Déclare l’application accounts auprès de Django."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
