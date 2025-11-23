from django.apps import AppConfig


class ListingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'

    def ready(self):
        """Importer les signaux au démarrage de l'application"""
        import listings.signals
