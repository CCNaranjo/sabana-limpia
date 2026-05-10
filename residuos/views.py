"""
residuos/views.py
=================
Vistas del módulo de residuos domésticos (ciudadano).

Vistas implementadas:
    NuevoRegistroView   → T-20: Crear o editar registro de la semana actual
    MisRegistrosView    → T-21: Historial personal con paginación

Principios aplicados:
    - CiudadanoRequeridoMixin centraliza autenticación + autorización.
    - Business logic separada de HTTP (métodos privados _get_or_init_form,
      _save_registro, etc.) para facilitar testing.
    - Todas las fechas pasan por utils.py — las vistas no calculan fechas
      directamente.
    - `get_object_or_404` siempre scoped a request.user — un ciudadano no
      puede acceder a registros de otro ciudadano.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from usuarios.decorators import rol_requerido

from .forms import NuevoRegistroForm
from .models import RegistroResiduo
from .utils import (
    format_week_range,
    get_week_bounds,
    get_week_start,
    is_editable,
)

logger = logging.getLogger(__name__)

# Semanas de historial en MisRegistros (T-21)
SEMANAS_HISTORIAL = 8
REGISTROS_POR_PAGINA = 10


# ---------------------------------------------------------------------------
# Mixin compartido
# ---------------------------------------------------------------------------

class CiudadanoRequeridoMixin:
    """
    Aplica @login_required y @rol_requerido('ciudadano') a toda la vista.

    Uso: heredar como primer mixin antes de View.
        class MiVista(CiudadanoRequeridoMixin, View): ...
    """

    @method_decorator(login_required)
    @method_decorator(rol_requerido('ciudadano'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# T-20 — Nuevo / Editar Registro
# ---------------------------------------------------------------------------

class NuevoRegistroView(CiudadanoRequeridoMixin, View):
    """
    GET  → Muestra formulario vacío o pre-llenado si ya existe un registro
           para la semana actual.
    POST → Guarda (crea o actualiza) el registro y redirige a mis-registros.

    Lógica de edición:
        El ciudadano puede editar el registro de la semana actual en cualquier
        momento, y el de la semana anterior solo si hoy es lunes o martes
        (ventana de corrección de 2 días — ver utils.is_editable).
    """

    template_name = 'residuos/nuevo_registro.html'

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get(self, request):
        semana_lunes, semana_domingo = get_week_bounds()

        registro = self._get_registro_actual(request.user, semana_lunes)
        form = NuevoRegistroForm(instance=registro)

        return render(request, self.template_name, self._build_context(
            form=form,
            semana_lunes=semana_lunes,
            semana_domingo=semana_domingo,
            es_edicion=bool(registro),
        ))

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------

    def post(self, request):
        semana_lunes, semana_domingo = get_week_bounds()

        registro = self._get_registro_actual(request.user, semana_lunes)
        form = NuevoRegistroForm(request.POST, instance=registro)

        if not form.is_valid():
            return render(request, self.template_name, self._build_context(
                form=form,
                semana_lunes=semana_lunes,
                semana_domingo=semana_domingo,
                es_edicion=bool(registro),
            ))

        self._save_registro(form, request, semana_lunes)

        accion = 'actualizado' if registro else 'creado'
        messages.success(
            request,
            f'Registro {accion} correctamente para la semana del '
            f'{format_week_range(semana_lunes)}.'
        )
        logger.info(
            'RegistroResiduo %s | usuario=%s | semana=%s | municipio=%s',
            accion,
            request.user.email,
            semana_lunes,
            request.user.municipio,
        )

        return redirect('residuos:mis_registros')

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _get_registro_actual(user, semana_lunes):
        """
        Busca el RegistroResiduo del usuario para la semana indicada.

        Returns:
            RegistroResiduo | None
        """
        return RegistroResiduo.objects.filter(
            usuario=user,
            semana=semana_lunes,
        ).first()

    @staticmethod
    def _save_registro(form: NuevoRegistroForm, request, semana_lunes) -> RegistroResiduo:
        """
        Guarda el registro completando los campos del servidor.

        commit=False permite asignar campos controlados por el servidor
        antes del INSERT/UPDATE definitivo, sin exposición al POST del cliente.
        """
        registro = form.save(commit=False)
        registro.usuario   = request.user
        registro.semana    = semana_lunes
        registro.municipio = request.user.municipio
        registro.save()
        return registro

    @staticmethod
    def _build_context(*, form, semana_lunes, semana_domingo, es_edicion) -> dict:
        """Construye el contexto del template de forma centralizada."""
        return {
            'form':          form,
            'semana_lunes':  semana_lunes,
            'semana_domingo': semana_domingo,
            'semana_label':  format_week_range(semana_lunes),
            'es_edicion':    es_edicion,
        }


# ---------------------------------------------------------------------------
# T-21 — Historial "Mis Registros"
# ---------------------------------------------------------------------------

class MisRegistrosView(CiudadanoRequeridoMixin, View):
    """
    Lista los registros de residuos del ciudadano logueado.

    Muestra las últimas SEMANAS_HISTORIAL semanas con paginación de
    REGISTROS_POR_PAGINA filas por página.

    Cada fila indica si puede editarse (is_editable del utils) para que
    el template muestre u oculte el botón de edición dinámicamente.
    """

    template_name = 'residuos/mis_registros.html'

    def get(self, request):
        from datetime import timedelta
        from .utils import get_week_start

        # Límite de 8 semanas hacia atrás
        semana_actual = get_week_start()
        semana_limite = semana_actual - timedelta(weeks=SEMANAS_HISTORIAL)

        registros_qs = (
            RegistroResiduo.objects
            .filter(usuario=request.user, semana__gte=semana_limite)
            .order_by('-semana')
        )

        # Anotar editabilidad sin tocar el modelo (se resuelve en Python)
        registros_con_meta = [
            {
                'obj':       r,
                'label':     format_week_range(r.semana),
                'total':     round(r.total_kg(), 2),
                'editable':  is_editable(r.semana),
            }
            for r in registros_qs
        ]

        # Paginación
        paginator = Paginator(registros_con_meta, REGISTROS_POR_PAGINA)
        page_number = request.GET.get('page', 1)
        page_obj    = paginator.get_page(page_number)

        return render(request, self.template_name, {
            'page_obj':      page_obj,
            'semana_actual': get_week_start(),
            'semana_label':  format_week_range(get_week_start()),
        })