from django.contrib import admin
from .models import Reporte


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display  = ('id', 'titulo', 'categoria', 'estado', 'municipio', 'usuario', 'created_at')
    list_filter   = ('estado', 'municipio', 'categoria')
    search_fields = ('titulo', 'descripcion', 'usuario__email')
    readonly_fields = ('created_at', 'updated_at')