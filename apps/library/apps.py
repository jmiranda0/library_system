from django.apps import AppConfig


class LibraryConfig(AppConfig):
    """Configuración de la aplicación principal de gestión bibliotecaria."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.library'
    verbose_name = 'Gestión Bibliotecaria'
