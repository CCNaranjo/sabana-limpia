from django.contrib import admin
from .models import RegistroResiduo


@admin.register(RegistroResiduo)
class RegistroResiduoAdmin(admin.ModelAdmin):
    list_display  = ('id', 'usuario', 'semana', 'municipio',
                     'organico_kg', 'reciclable_kg', 'no_reciclable_kg',
                     'especial_kg', 'peligroso_kg')
    list_filter   = ('municipio', 'semana')
    search_fields = ('usuario__email',)
    readonly_fields = ('created_at',)