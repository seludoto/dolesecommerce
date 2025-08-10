from django.apps import AppConfig


class StoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stores'
    verbose_name = 'Store Management'
    
    def ready(self):
        # Import signals when they are created
        # import stores.signals
        pass
