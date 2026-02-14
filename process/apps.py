# process/apps.py
from django.apps import AppConfig

class ProcessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'process'

    def ready(self):
        # Remove this:
        # from rent.utils import create_superuser
        # create_superuser()
        import process.signals  # <-- optional, if you use signals
