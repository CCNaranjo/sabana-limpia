import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from usuarios.decorators import rol_requerido
from reportes.models import Reporte

logger = logging.getLogger(__name__)


class OperadorRequeridoMixin:
    @method_decorator(login_required)
    @method_decorator(rol_requerido('operador', 'admin'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class ListaReportesView(OperadorRequeridoMixin, View):
    """
    T-25 — Panel operador: lista de reportes de su municipio.
    Soporta filtros GET por estado y categoría (T-27).
    """
    template_name = 'panel/lista_reportes.html'

    def get(self, request):
        estado    = request.GET.get('estado', '')
        categoria = request.GET.get('categoria', '')

        reportes = Reporte.objects.filter(
            municipio=request.user.municipio
        ).order_by('-created_at')

        if estado:
            reportes = reportes.filter(estado=estado)
        if categoria:
            reportes = reportes.filter(categoria=categoria)

        return render(request, self.template_name, {
            'reportes':        reportes,
            'estado_actual':   estado,
            'categoria_actual': categoria,
            'estados':         Reporte.Estado.choices,
            'categorias':      Reporte.Categoria.choices,
        })


class DetalleReporteView(OperadorRequeridoMixin, View):
    """
    T-26 — Detalle y cambio de estado de un reporte.
    Solo operadores del mismo municipio pueden gestionar el reporte.
    """
    template_name = 'panel/detalle_reporte.html'

    def get(self, request, pk):
        reporte = get_object_or_404(
            Reporte,
            pk=pk,
            municipio=request.user.municipio
        )
        return render(request, self.template_name, {
            'reporte':  reporte,
            'estados':  Reporte.Estado.choices,
        })

    def post(self, request, pk):
        reporte = get_object_or_404(
            Reporte,
            pk=pk,
            municipio=request.user.municipio
        )

        nuevo_estado   = request.POST.get('estado')
        nota_operador  = request.POST.get('nota_operador', '').strip()

        # Validar que el estado es válido
        estados_validos = [e[0] for e in Reporte.Estado.choices]
        if nuevo_estado not in estados_validos:
            messages.error(request, 'Estado no válido.')
            return redirect('panel:detalle', pk=pk)

        # Nota obligatoria si resuelto o rechazado
        if nuevo_estado in ('resuelto', 'rechazado') and not nota_operador:
            messages.error(request, 'La nota es obligatoria al resolver o rechazar un reporte.')
            return render(request, self.template_name, {
                'reporte': reporte,
                'estados': Reporte.Estado.choices,
            })

        reporte.estado        = nuevo_estado
        reporte.nota_operador = nota_operador
        reporte.operador      = request.user
        reporte.save()

        logger.info(
            'Reporte #%s actualizado a "%s" por %s',
            reporte.pk, nuevo_estado, request.user.email
        )
        messages.success(request, f'Reporte #{reporte.pk} actualizado a "{reporte.get_estado_display()}".')
        return redirect('panel:lista')