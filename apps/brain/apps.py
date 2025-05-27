from django.apps import AppConfig


class BrainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.brain'
    verbose_name = 'Sisimpur Brain'

    def ready(self):
        """Initialize the brain app when Django starts"""
        # Import signal handlers if any
        pass
