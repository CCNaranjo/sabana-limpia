"""
URL configuration for the reportes app.

Routes:
    /reportes/nuevo/                → NuevoReporteView  (ciudadano)
    /reportes/mis-reportes/         → MisReportesView   (ciudadano)
    /reportes/confirmacion/<pk>/    → confirmacion      (ciudadano)

All routes require an active session. Role enforcement is handled in each view.
"""

from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("nuevo/", views.NuevoReporteView.as_view(), name="nuevo_reporte"),
    path("mis-reportes/", views.MisReportesView.as_view(), name="mis_reportes"),
    path("mapa-json/", views.MapaJsonView.as_view(), name="mapa_json"),
    path("mapa/", views.MapaView.as_view(), name="mapa"),
    path(
        "confirmacion/<int:pk>/",
        views.ConfirmacionView.as_view(),
        name="confirmacion",
    ),
]