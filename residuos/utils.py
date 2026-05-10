"""
residuos/utils.py
=================
Funciones auxiliares para el manejo de semanas en el módulo de residuos.

Se aíslan aquí (y no en views.py) para que sean:
- Testeables de forma independiente
- Reutilizables en vistas, serializers, tareas Celery (futuro)
- Fáciles de encontrar cuando cambien los requisitos de fecha

Todas las operaciones usan `django.utils.timezone` para ser correctas
con el huso horario configurado en settings.py (TIME_ZONE = 'America/Bogota').
"""

from datetime import date, timedelta

from django.utils import timezone


# ---------------------------------------------------------------------------
# Cálculo de semana
# ---------------------------------------------------------------------------

def get_week_start(ref: date | None = None) -> date:
    """
    Retorna el lunes (inicio) de la semana de `ref`.

    Args:
        ref: Fecha de referencia. Si es None usa hoy (zona horaria del proyecto).

    Returns:
        date: El lunes de esa semana.

    Ejemplos:
        Miércoles 5-dic → Lunes 3-dic
        Lunes 3-dic     → Lunes 3-dic
        Domingo 2-dic   → Lunes 26-nov
    """
    if ref is None:
        ref = timezone.localdate()   # Respeta TIME_ZONE de settings.py

    # weekday(): 0=lunes … 6=domingo
    return ref - timedelta(days=ref.weekday())


def get_week_bounds(ref: date | None = None) -> tuple[date, date]:
    """
    Retorna (lunes, domingo) de la semana de `ref`.

    Returns:
        tuple: (date_lunes, date_domingo)
    """
    monday = get_week_start(ref)
    sunday = monday + timedelta(days=6)
    return monday, sunday


# ---------------------------------------------------------------------------
# Formateo de semana
# ---------------------------------------------------------------------------

MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo',  6: 'junio',   7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre',
}


def format_week_range(monday: date) -> str:
    """
    Formatea el rango de una semana en español.

    Args:
        monday: El lunes de la semana.

    Returns:
        str: "3 al 9 de diciembre" | "28 de nov al 4 de diciembre"

    Si lunes y domingo son del mismo mes → "3 al 9 de diciembre"
    Si cruzan meses                      → "28 de noviembre al 4 de diciembre"
    """
    sunday = monday + timedelta(days=6)

    mes_lunes  = MESES_ES[monday.month]
    mes_domingo = MESES_ES[sunday.month]

    if monday.month == sunday.month:
        return f"{monday.day} al {sunday.day} de {mes_domingo}"
    else:
        return f"{monday.day} de {mes_lunes} al {sunday.day} de {mes_domingo}"


# ---------------------------------------------------------------------------
# Ventana de edición
# ---------------------------------------------------------------------------

def is_editable(semana_lunes: date) -> bool:
    """
    Determina si un registro puede ser editado por el ciudadano.

    Reglas:
        - La semana registrada es la semana actual → siempre editable.
        - La semana registrada es la anterior → editable solo si hoy es
          lunes o martes (ventana de 2 días para corrección de errores).
        - Semanas anteriores → no editables.

    Args:
        semana_lunes: El campo `semana` del RegistroResiduo.

    Returns:
        bool: True si el ciudadano puede editar, False si es de solo lectura.
    """
    today      = timezone.localdate()
    this_week  = get_week_start(today)
    prev_week  = this_week - timedelta(weeks=1)

    # Semana actual → siempre editable
    if semana_lunes == this_week:
        return True

    # Semana anterior → editable solo lunes y martes de la semana siguiente
    if semana_lunes == prev_week:
        return today.weekday() <= 1   # 0=lunes, 1=martes

    return False