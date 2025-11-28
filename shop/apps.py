from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'Green Shop'

    def ready(self):
        # Import signals to ensure user profiles are created automatically.
        from . import signals  # noqa: F401