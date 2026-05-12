"""
config/views.py
===============
Vistas globales del proyecto SabanaLimpia.

La landing page vive aquí y no en ninguna app específica porque pertenece
al proyecto completo, no a un dominio de negocio (usuarios, reportes, residuos).
"""

from django.views.generic import TemplateView

from reportes.models import Reporte
from residuos.models import RegistroResiduo


class LandingView(TemplateView):
    """
    GET /

    Página de inicio pública. No requiere autenticación.

    Contexto inyectado:
        total_reportes   (int): Total histórico de reportes recibidos.
        total_resueltos  (int): Reportes con estado 'resuelto'.
        total_municipios (int): Municipios cubiertos (constante 11).
        total_registros  (int): Registros domésticos de residuos ingresados.

    Decisión: Queries directas y simples (COUNT en BD) — sin anotaciones
    complejas. En el futuro pueden cachearse con django.core.cache si el
    tráfico lo justifica (T-35).
    """

    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["total_reportes"]   = Reporte.objects.count()
        ctx["total_resueltos"]  = Reporte.objects.filter(
            estado=Reporte.Estado.RESUELTO
        ).count()
        ctx["total_municipios"] = 11
        ctx["total_registros"]  = RegistroResiduo.objects.count()

        return ctx