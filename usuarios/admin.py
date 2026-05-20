"""
usuarios/admin.py
=================
Panel de administración para CustomUser.

Acciones en lote implementadas:
    - activar_usuarios        → is_active = True
    - desactivar_usuarios     → is_active = False
    - promover_a_operador     → rol = 'operador'
    - revertir_a_ciudadano    → rol = 'ciudadano'
"""

from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Insignia, LogroUsuario


@admin.register(Insignia)
class InsigniaAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'slug', 'nivel', 'emoji', 'visible', 'orden')
    list_filter   = ('nivel', 'visible')
    search_fields = ('nombre', 'slug')
    ordering      = ('-nivel', 'orden')


@admin.register(LogroUsuario)
class LogroUsuarioAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'insignia', 'fecha_obtencion', 'notificado')
    list_filter   = ('insignia__nivel', 'notificado')
    search_fields = ('usuario__email', 'insignia__nombre')
    raw_id_fields = ('usuario',)

# ---------------------------------------------------------------------------
# Acciones en lote
# ---------------------------------------------------------------------------

@admin.action(description="✅ Activar usuarios seleccionados")
def activar_usuarios(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        f"{updated} usuario(s) activado(s) correctamente.",
        messages.SUCCESS,
    )


@admin.action(description="🚫 Desactivar usuarios seleccionados")
def desactivar_usuarios(modeladmin, request, queryset):
    # Proteger superusuarios
    superusers = queryset.filter(is_superuser=True).count()
    if superusers:
        modeladmin.message_user(
            request,
            f"No se pueden desactivar {superusers} superusuario(s). "
            "El resto fue procesado.",
            messages.WARNING,
        )
    updated = queryset.filter(is_superuser=False).update(is_active=False)
    if updated:
        modeladmin.message_user(
            request,
            f"{updated} usuario(s) desactivado(s).",
            messages.SUCCESS,
        )


@admin.action(description="🔧 Promover a operador")
def promover_a_operador(modeladmin, request, queryset):
    updated = queryset.filter(is_superuser=False).update(rol='operador', is_staff=True)
    modeladmin.message_user(
        request,
        f"{updated} usuario(s) promovido(s) a operador.",
        messages.SUCCESS,
    )


@admin.action(description="👤 Revertir a ciudadano")
def revertir_a_ciudadano(modeladmin, request, queryset):
    updated = queryset.filter(is_superuser=False).update(rol='ciudadano', is_staff=False)
    modeladmin.message_user(
        request,
        f"{updated} usuario(s) revertido(s) a ciudadano.",
        messages.SUCCESS,
    )


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    # ── Listado ────────────────────────────────────────────────────────────
    list_display        = ('email', 'get_full_name', 'rol', 'municipio', 'is_active', 'is_staff', 'date_joined')
    list_display_links  = ('email',)
    list_filter         = ('rol', 'municipio', 'is_active', 'is_staff')
    list_per_page       = 25
    date_hierarchy      = 'date_joined'

    # ── Búsqueda ───────────────────────────────────────────────────────────
    search_fields = ('email', 'first_name', 'last_name', 'municipio')

    # ── Ordenamiento ───────────────────────────────────────────────────────
    ordering = ('-date_joined',)

    # ── Acciones en lote ───────────────────────────────────────────────────
    actions = [
        activar_usuarios,
        desactivar_usuarios,
        promover_a_operador,
        revertir_a_ciudadano,
    ]

    # ── Campos en formulario de detalle ────────────────────────────────────
    # Extiende el fieldsets de UserAdmin para agregar los campos propios
    fieldsets = UserAdmin.fieldsets + (
        ('SabanaLimpia', {
            'fields': ('rol', 'municipio'),
        }),
    )

    # Campos visibles al CREAR un usuario desde el admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('SabanaLimpia', {
            'fields': ('email', 'rol', 'municipio'),
        }),
    )

    # Auditoría — no editables
    readonly_fields = ('date_joined', 'last_login')