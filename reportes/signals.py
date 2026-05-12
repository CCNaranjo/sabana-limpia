import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Reporte

logger = logging.getLogger(__name__)

# Guardamos el estado anterior para detectar cambios
_estado_anterior = {}


@receiver(post_save, sender=Reporte)
def notificar_cambio_estado(sender, instance, created, **kwargs):
    """
    Envía email al ciudadano cuando el operador cambia el estado del reporte.
    En desarrollo imprime en consola gracias a EMAIL_BACKEND de settings.
    """
    if created:
        # Guardar estado inicial, no notificar al crear
        _estado_anterior[instance.pk] = instance.estado
        return

    estado_previo = _estado_anterior.get(instance.pk)

    if estado_previo == instance.estado:
        return  # No hubo cambio de estado

    # Actualizar caché
    _estado_anterior[instance.pk] = instance.estado

    asunto = f'[SabanaLimpia] Tu reporte #{instance.pk} fue actualizado'
    mensaje = (
        f'Hola,\n\n'
        f'Tu reporte "{instance.titulo}" (#{instance.pk}) '
        f'ha cambiado de estado a: {instance.get_estado_display()}.\n\n'
    )

    if instance.nota_operador:
        mensaje += f'Nota del operador:\n{instance.nota_operador}\n\n'

    mensaje += 'Puedes ver el estado en: http://localhost:8000/reportes/mis-reportes/\n\nEquipo SabanaLimpia'

    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.usuario.email],
            fail_silently=False,
        )
        logger.info('Email enviado a %s por cambio de estado reporte #%s', instance.usuario.email, instance.pk)
    except Exception as e:
        logger.error('Error enviando email reporte #%s: %s', instance.pk, e)