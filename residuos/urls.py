"""
residuos/urls.py
================
Rutas del módulo de residuos domésticos.

    /residuos/nuevo/          → NuevoRegistroView  [ciudadano]
    /residuos/mis-registros/  → MisRegistrosView   [ciudadano]

T-29 y T-30 agregarán en el futuro:
    /residuos/estadisticas/           → Estadísticas públicas
    /api/residuos/estadisticas/       → JSON para Chart.js
"""

from django.urls import path

from . import views

app_name = 'residuos'

urlpatterns = [
    path('nuevo/',         views.NuevoRegistroView.as_view(), name='nuevo_registro'),
    path('mis-registros/', views.MisRegistrosView.as_view(),  name='mis_registros'),
    path('estadisticas/',     views.EstadisticasView.as_view(),     name='estadisticas'),
    path('estadisticas-json/', views.EstadisticasJsonView.as_view(), name='estadisticas_json'),
]