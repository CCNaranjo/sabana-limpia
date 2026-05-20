import logging
from django.apps import AppConfig


logger = logging.getLogger(__name__)


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        import usuarios.signals  # noqa: F401 — importar para registrar los receivers

