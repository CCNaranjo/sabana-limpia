"""
residuos/admin.py
=================
Panel de administración para RegistroResiduo.

Correcciones sobre la versión anterior:
    - total_kg_display: ordering eliminado — no se puede ordenar por un
      método Python sin anotación de queryset. La versión anterior apuntaba
      a 'organico_kg', lo que ordenaba por ese campo, no por el total real.
    - Acciones en lote agregadas.

Acciones en lote implementadas:
    - exportar_resumen_csv  → descarga CSV con totales por usuario y semana
    - limpiar_observaciones → vacía el campo observaciones de los seleccionados
"""

import csv

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse

from .models import RegistroResiduo


# ---------------------------------------------------------------------------
# Acciones en lote
# ---------------------------------------------------------------------------

@admin.action(description="📥 Exportar selección a CSV")
def exportar_resumen_csv(modeladmin, request, queryset):
    """
    Genera un archivo CSV descargable con los registros seleccionados.

    Columnas: email_usuario, semana, municipio, organico_kg, reciclable_kg,
              no_reciclable_kg, especial_kg, peligroso_kg, total_kg.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="registros_residuos.csv"'

    # BOM para que Excel en español abra correctamente el UTF-8
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'Email ciudadano',
        'Semana (lunes)',
        'Municipio',
        'Orgánico (kg)',
        'Reciclable (kg)',
        'No reciclable (kg)',
        'Especial (kg)',
        'Peligroso (kg)',
        'Total (kg)',
    ])

    for registro in queryset.select_related('usuario').order_by('-semana'):
        writer.writerow([
            registro.usuario.email,
            registro.semana.strftime('%Y-%m-%d'),
            registro.get_municipio_display(),
            registro.organico_kg,
            registro.reciclable_kg,
            registro.no_reciclable_kg,
            registro.especial_kg,
            registro.peligroso_kg,
            round(registro.total_kg(), 2),
        ])

    modeladmin.message_user(
        request,
        f"CSV generado con {queryset.count()} registro(s).",
        messages.SUCCESS,
    )
    return response


@admin.action(description="🗑️ Limpiar observaciones de seleccionados")
def limpiar_observaciones(modeladmin, request, queryset):
    updated = queryset.update(observaciones=None)
    modeladmin.message_user(
        request,
        f"Observaciones eliminadas en {updated} registro(s).",
        messages.WARNING,
    )


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@admin.register(RegistroResiduo)
class RegistroResiduoAdmin(admin.ModelAdmin):

    # ── Listado ────────────────────────────────────────────────────────────
    list_display = (
        'usuario',
        'semana',
        'municipio',
        'organico_kg',
        'reciclable_kg',
        'no_reciclable_kg',
        'especial_kg',
        'peligroso_kg',
        'total_kg_display',
        'created_at',
    )
    list_display_links  = ('usuario', 'semana')
    list_filter         = ('municipio', 'semana')
    list_per_page       = 25
    date_hierarchy      = 'semana'

    # ── Búsqueda ───────────────────────────────────────────────────────────
    search_fields = ('usuario__email', 'municipio')

    # ── Ordenamiento ───────────────────────────────────────────────────────
    ordering = ('-semana',)

    # ── Acciones en lote ───────────────────────────────────────────────────
    actions = [exportar_resumen_csv, limpiar_observaciones]

    # ── Campos de solo lectura ─────────────────────────────────────────────
    readonly_fields = ('created_at', 'updated_at')

    # ── Campos en formulario de detalle ────────────────────────────────────
    fieldsets = (
        ('Identificación', {
            'fields': ('usuario', 'semana', 'municipio'),
        }),
        ('Residuos (kg)', {
            'fields': (
                'organico_kg',
                'reciclable_kg',
                'no_reciclable_kg',
                'especial_kg',
                'peligroso_kg',
            ),
        }),
        ('Notas', {
            'fields': ('observaciones',),
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Columnas calculadas ────────────────────────────────────────────────

    @admin.display(description='Total (kg)')
    def total_kg_display(self, obj):
        """
        Muestra la suma de todos los tipos de residuo.

        Sin parámetro `ordering`: total_kg() es un método Python y Django
        Admin no puede delegar el ORDER BY a la BD sin una anotación previa
        en get_queryset(). Agregarlo en el futuro si se necesita ordenar.
        """
        return f'{obj.total_kg():.2f} kg'