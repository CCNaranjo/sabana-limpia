"""
Motor central de verificación y asignación de insignias.

Uso:
    from usuarios.badges import verificar_y_otorgar_insignias
    nuevas = verificar_y_otorgar_insignias(usuario)
    # nuevas: lista de objetos Insignia recién obtenidos (para notificar)
"""

from .models import Insignia, LogroUsuario
from reportes.models import Reporte
from residuos.models import RegistroResiduo
from datetime import date, timedelta


def verificar_y_otorgar_insignias(usuario):
    """
    Verifica todas las insignias activas contra el estado actual del usuario.
    Crea LogroUsuario para las que se cumplen por primera vez.
    Devuelve la lista de Insignia recién obtenidas (para mostrar en toast).
    """
    stats   = _obtener_estadisticas(usuario)
    nuevas  = []

    for insignia in Insignia.objects.all():
        ya_tiene = LogroUsuario.objects.filter(
            usuario=usuario, insignia=insignia
        ).exists()

        if ya_tiene:
            continue

        if _cumple_condicion(insignia.condicion, stats, usuario):
            LogroUsuario.objects.create(
                usuario=usuario,
                insignia=insignia,
                notificado=False,
            )
            nuevas.append(insignia)

    return nuevas


def _obtener_estadisticas(usuario):
    """
    Recopila todas las métricas relevantes del usuario en un solo lugar.
    Se llama una vez por verificación para evitar múltiples queries.
    """
    mis_reportes = Reporte.objects.filter(usuario=usuario)
    mis_residuos = RegistroResiduo.objects.filter(usuario=usuario)

    total_reportes     = mis_reportes.count()
    reportes_resueltos = mis_reportes.filter(estado='resuelto').count()

    municipios_distintos = (
        mis_reportes.values_list('municipio', flat=True)
        .distinct().count()
    )
    categorias_distintas = (
        mis_reportes.values_list('categoria', flat=True)
        .distinct().count()
    )

    total_registros = mis_residuos.count()

    semanas_consecutivas = _calcular_semanas_consecutivas(usuario)

    reporto_municipio_virgen = _verificar_municipio_virgen(usuario)

    return {
        'total_reportes':          total_reportes,
        'reportes_resueltos':      reportes_resueltos,
        'municipios_distintos':    municipios_distintos,
        'categorias_distintas':    categorias_distintas,
        'total_registros_residuos': total_registros,
        'semanas_consecutivas':    semanas_consecutivas,
        'municipio_virgen':        reporto_municipio_virgen,
    }


def _calcular_semanas_consecutivas(usuario):
    """
    Cuenta cuántas semanas seguidas (hacia atrás desde hoy) el usuario
    tiene al menos un RegistroResiduo.
    """
    semanas = set(
        RegistroResiduo.objects.filter(usuario=usuario)
        .values_list('semana', flat=True)
    )
    if not semanas:
        return 0

    hoy         = date.today()
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    contador    = 0
    semana_check = lunes_actual

    while semana_check in semanas:
        contador    += 1
        semana_check = semana_check - timedelta(weeks=1)

    return contador


def _verificar_municipio_virgen(usuario):
    """
    Devuelve True si alguno de los municipios donde el usuario reportó
    no tenía ningún reporte de otro usuario en el momento del primer
    reporte de este usuario (aproximación: si el usuario fue el primero en reportar ahí).
    """
    mis_municipios = (
        Reporte.objects.filter(usuario=usuario)
        .values_list('municipio', flat=True)
        .distinct()
    )

    for municipio in mis_municipios:
        primer_reporte_municipio = (
            Reporte.objects.filter(municipio=municipio)
            .order_by('created_at')
            .first()
        )
        if primer_reporte_municipio and primer_reporte_municipio.usuario == usuario:
            return True

    return False


def _cumple_condicion(condicion, stats, usuario):
    """Evalúa si las estadísticas actuales satisfacen la condición de una insignia."""
    tipo = condicion.get('tipo')

    if tipo == 'total_reportes':
        return stats['total_reportes'] >= condicion['umbral']

    if tipo == 'reportes_resueltos':
        return stats['reportes_resueltos'] >= condicion['umbral']

    if tipo == 'municipios_distintos':
        return stats['municipios_distintos'] >= condicion['umbral']

    if tipo == 'categorias_distintas':
        return stats['categorias_distintas'] >= condicion['umbral']

    if tipo == 'total_registros_residuos':
        return stats['total_registros_residuos'] >= condicion['umbral']

    if tipo == 'semanas_consecutivas':
        return stats['semanas_consecutivas'] >= condicion['umbral']

    if tipo == 'primer_reporte_municipio_virgen':
        return stats['municipio_virgen']

    return False