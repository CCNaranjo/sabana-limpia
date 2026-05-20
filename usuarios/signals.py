"""
Signals que disparan la verificación de insignias después de
los eventos relevantes del sistema.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from reportes.models import Reporte
from residuos.models import RegistroResiduo

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Reporte)
def verificar_insignias_reporte(sender, instance, created, **kwargs):
    """
    Se ejecuta cada vez que se crea o actualiza un Reporte.
    Verifica insignias para el usuario que creó el reporte.
    """
    from usuarios.badges import verificar_y_otorgar_insignias
    nuevas = verificar_y_otorgar_insignias(instance.usuario)
    if nuevas:
        _guardar_en_sesion_pendiente(instance.usuario, nuevas)


@receiver(post_save, sender=RegistroResiduo)
def verificar_insignias_residuo(sender, instance, created, **kwargs):
    """
    Se ejecuta cada vez que se crea un RegistroResiduo.
    """
    if not created:
        return
    from usuarios.badges import verificar_y_otorgar_insignias
    nuevas = verificar_y_otorgar_insignias(instance.usuario)
    if nuevas:
        _guardar_en_sesion_pendiente(instance.usuario, nuevas)


def _guardar_en_sesion_pendiente(usuario, insignias_nuevas):
    """
    Marca las insignias como pendientes de notificación.
    El toast las leerá en la próxima carga de página.
    """
    # Marcar los LogroUsuario como 'a notificar'
    from usuarios.models import LogroUsuario
    LogroUsuario.objects.filter(
        usuario=usuario,
        insignia__in=insignias_nuevas,
        notificado=False
    ).update(notificado=False)  # ya está en False por defecto, es el estado correcto