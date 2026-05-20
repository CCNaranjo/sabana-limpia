"""
reportes/admin.py
=================
Panel de administración para Reporte.

Acciones en lote implementadas:
    - marcar_pendiente     → estado = 'pendiente'
    - marcar_en_gestion    → estado = 'en_gestion'
    - marcar_resuelto      → estado = 'resuelto'
    - marcar_rechazado     → estado = 'rechazado'

Estas acciones replican lo que el operador hace en su panel (T-25/T-26)
pero de forma masiva desde /admin/, útil para pruebas y correcciones.
"""

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .models import Reporte


# ---------------------------------------------------------------------------
# Acciones en lote
# ---------------------------------------------------------------------------

@admin.action(description="🕐 Marcar como Pendiente")
def marcar_pendiente(modeladmin, request, queryset):
    updated = queryset.update(estado=Reporte.Estado.PENDIENTE)
    modeladmin.message_user(
        request,
        f"{updated} reporte(s) marcado(s) como Pendiente.",
        messages.SUCCESS,
    )


@admin.action(description="🔵 Marcar como En Gestión")
def marcar_en_gestion(modeladmin, request, queryset):
    updated = queryset.update(estado=Reporte.Estado.EN_GESTION)
    modeladmin.message_user(
        request,
        f"{updated} reporte(s) marcado(s) como En Gestión.",
        messages.SUCCESS,
    )


@admin.action(description="✅ Marcar como Resuelto")
def marcar_resuelto(modeladmin, request, queryset):
    updated = queryset.update(estado=Reporte.Estado.RESUELTO)
    modeladmin.message_user(
        request,
        f"{updated} reporte(s) marcado(s) como Resuelto.",
        messages.SUCCESS,
    )


@admin.action(description="❌ Marcar como Rechazado")
def marcar_rechazado(modeladmin, request, queryset):
    updated = queryset.update(estado=Reporte.Estado.RECHAZADO)
    modeladmin.message_user(
        request,
        f"{updated} reporte(s) marcado(s) como Rechazado.",
        messages.WARNING,
    )


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):

    # ── Listado ────────────────────────────────────────────────────────────
    list_display        = (
        'id',
        'titulo',
        'categoria',
        'estado_badge',
        'municipio',
        'usuario',
        'operador',
        'created_at',
        'updated_at',
    )
    list_display_links  = ('id', 'titulo')
    list_filter         = ('estado', 'municipio', 'categoria')
    list_per_page       = 25
    date_hierarchy      = 'created_at'

    # ── Búsqueda ───────────────────────────────────────────────────────────
    search_fields = ('titulo', 'descripcion', 'usuario__email', 'municipio')

    # ── Ordenamiento ───────────────────────────────────────────────────────
    ordering = ('-created_at',)

    # ── Acciones en lote ───────────────────────────────────────────────────
    actions = [
        marcar_pendiente,
        marcar_en_gestion,
        marcar_resuelto,
        marcar_rechazado,
    ]

    # ── Campos de solo lectura ─────────────────────────────────────────────
    readonly_fields = ('created_at', 'updated_at', 'estado_badge_detail')

    # ── Campos en formulario de detalle ────────────────────────────────────
    fieldsets = (
        ('Información del reporte', {
            'fields': ('usuario', 'titulo', 'descripcion', 'foto'),
        }),
        ('Clasificación', {
            'fields': ('categoria', 'municipio'),
        }),
        ('Ubicación', {
            'fields': ('latitud', 'longitud'),
        }),
        ('Gestión operativa', {
            'fields': ('estado', 'operador', 'nota_operador'),
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Columnas calculadas ────────────────────────────────────────────────

    # Colores de badge por estado para visualización en listado
    _COLORES_ESTADO = {
        Reporte.Estado.PENDIENTE:  ('#fff3cd', '#856404'),
        Reporte.Estado.EN_GESTION: ('#cce5ff', '#004085'),
        Reporte.Estado.RESUELTO:   ('#d4edda', '#155724'),
        Reporte.Estado.RECHAZADO:  ('#f8d7da', '#721c24'),
    }

    @admin.display(description='Estado', ordering='estado')
    def estado_badge(self, obj):
        """Muestra el estado como badge de color en el listado."""
        bg, color = self._COLORES_ESTADO.get(obj.estado, ('#eee', '#333'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;'
            'border-radius:4px;font-size:0.82em;font-weight:600;">{}</span>',
            bg, color, obj.get_estado_display(),
        )

    @admin.display(description='Estado actual')
    def estado_badge_detail(self, obj):
        """Versión más grande del badge para la vista de detalle."""
        bg, color = self._COLORES_ESTADO.get(obj.estado, ('#eee', '#333'))
        return format_html(
            '<span style="background:{};color:{};padding:4px 14px;'
            'border-radius:6px;font-size:1em;font-weight:700;">{}</span>',
            bg, color, obj.get_estado_display(),
        )