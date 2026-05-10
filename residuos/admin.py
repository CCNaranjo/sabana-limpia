"""
residuos/admin.py
=================
Registro del modelo RegistroResiduo en el panel de administración de Django.

Configuración orientada a la gestión operativa:
    - list_display: Columnas más útiles para supervisar registros
    - list_filter:  Filtros laterales para explorar por municipio y semana
    - search_fields: Búsqueda por email del ciudadano
    - readonly_fields: Evita edición accidental de campos de auditoría
"""

from django.contrib import admin

from .models import RegistroResiduo


@admin.register(RegistroResiduo)
class RegistroResiduoAdmin(admin.ModelAdmin):

    # Columnas visibles en el listado
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

    # Filtros laterales
    list_filter = ('municipio', 'semana')

    # Búsqueda por email del ciudadano
    search_fields = ('usuario__email',)

    # Ordenamiento por defecto (semana más reciente primero)
    ordering = ('-semana',)

    # Campos de solo lectura (no se pueden editar desde el admin)
    readonly_fields = ('created_at', 'updated_at')

    # Agrupación de campos en el formulario de detalle
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

    # ------------------------------------------------------------------
    # Columnas calculadas
    # ------------------------------------------------------------------

    @admin.display(description='Total (kg)', ordering='organico_kg')
    def total_kg_display(self, obj):
        return f'{obj.total_kg():.2f} kg'