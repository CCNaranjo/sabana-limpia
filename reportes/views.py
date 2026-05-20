"""
Views for the reportes app.

Design decisions:
- All views are Class-Based (CBV) for consistency and easier method-level overrides.
- Role enforcement uses the project's @rol_requerido decorator applied via
  method_decorator on dispatch(), so it runs before GET and POST alike.
- Business logic that doesn't belong in templates (e.g. completing the Reporte
  object before saving) lives in _build_reporte(), keeping post() readable.
- ConfirmacionView uses get_object_or_404 scoped to request.user so citizens
  can never access each other's confirmation pages by guessing a PK.
"""

import logging
import json
from django.http import JsonResponse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from usuarios.decorators import rol_requerido

from .forms import NuevoReporteForm
from .models import Reporte

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mixins / shared helpers
# ---------------------------------------------------------------------------

class CiudadanoRequeridoMixin:
    """
    Enforces login + ciudadano role on every method of the view.

    Using a mixin instead of repeating the decorator stack on each class keeps
    the code DRY and makes it easy to extend (e.g. add rate-limiting later).
    """

    @method_decorator(login_required)
    @method_decorator(rol_requerido("ciudadano"))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# T-17 — Nuevo Reporte
# ---------------------------------------------------------------------------

class NuevoReporteView(CiudadanoRequeridoMixin, View):
    """
    GET  → Render the empty report form.
    POST → Validate, save the Reporte and redirect to the confirmation page.

    The citizen never touches: usuario, municipio, estado, operador, nota_operador.
    Those fields are set here programmatically.
    """

    template_name = "reportes/nuevo_reporte.html"

    def get(self, request):
        form = NuevoReporteForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = NuevoReporteForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        reporte = self._save_reporte(form, request)
        logger.info(
            "Nuevo reporte creado: id=%s usuario=%s municipio=%s",
            reporte.pk,
            request.user.email,
            reporte.municipio,
        )
        return redirect("reportes:confirmacion", pk=reporte.pk)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _save_reporte(form: NuevoReporteForm, request) -> Reporte:
        """
        Commits the Reporte to DB with server-controlled fields.

        Using commit=False lets us set fields that the citizen must NOT
        control before the final INSERT, following the principle of
        least-privilege on form data.
        """
        reporte = form.save(commit=False)
        reporte.usuario = request.user
        reporte.municipio = request.user.municipio
        reporte.estado = Reporte.Estado.PENDIENTE
        reporte.save()
        return reporte


# ---------------------------------------------------------------------------
# T-19 — Mis Reportes
# ---------------------------------------------------------------------------

class MisReportesView(CiudadanoRequeridoMixin, View):
    """
    Lists all reports filed by the logged-in citizen, ordered newest first.

    Pagination is not implemented in T-19 but the queryset is structured so
    adding Django's Paginator in a future sprint requires changing only this view.
    """

    template_name = "reportes/mis_reportes.html"

    def get(self, request):
        reportes = (
            Reporte.objects.filter(usuario=request.user)
            .order_by("-created_at")
            .only(
                # Fetch only the columns the template actually uses.
                # Avoids loading large TextField (descripcion) in list views.
                "id",
                "titulo",
                "categoria",
                "municipio",
                "estado",
                "foto",
                "created_at",
                "nota_operador",
            )
        )
        return render(request, self.template_name, {"reportes": reportes})


# ---------------------------------------------------------------------------
# T-22 — Confirmación post-reporte
# ---------------------------------------------------------------------------

class ConfirmacionView(CiudadanoRequeridoMixin, View):
    """
    Shows the citizen immediate feedback after submitting a report.

    Security note: the queryset is scoped to request.user so a citizen
    cannot view another citizen's confirmation page by manipulating the URL.
    """

    template_name = "reportes/confirmacion.html"

    def get(self, request, pk: int):
        reporte = get_object_or_404(Reporte, pk=pk, usuario=request.user)
        return render(request, self.template_name, {"reporte": reporte})
    
# ---------------------------------------------------------------------------
# T-23 — Endpoint JSON para el mapa
# ---------------------------------------------------------------------------

class MapaJsonView(View):
    """
    GET /api/reportes/mapa/
    Devuelve JSON con los reportes para Leaflet.js.
    Sin autenticación — es un endpoint público.
    Solo expone los campos necesarios para los markers del mapa.
    """

    def get(self, request):
        reportes = (
            Reporte.objects
            .exclude(estado=Reporte.Estado.RECHAZADO)
            .only('id', 'latitud', 'longitud', 'categoria', 'estado', 'municipio', 'titulo')
            .values('id', 'latitud', 'longitud', 'categoria', 'estado', 'municipio', 'titulo')
        )

        return JsonResponse({'reportes': list(reportes)})
    
# ---------------------------------------------------------------------------
# T-24 — Mapa público
# ---------------------------------------------------------------------------

class MapaView(View):
    """Página pública del mapa de reportes. No requiere autenticación."""
    template_name = "reportes/mapa.html"

    def get(self, request):
        return render(request, self.template_name)
    
@login_required
def mapa_personal_json(request):
    """Devuelve los reportes del usuario logueado para el mapa de Mi Impacto."""
    puntos = (
        Reporte.objects
        .filter(usuario=request.user)
        .values('id', 'titulo', 'latitud', 'longitud', 'categoria', 'estado', 'municipio')
    )
    return JsonResponse({'puntos': list(puntos)})