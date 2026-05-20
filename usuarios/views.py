from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views import View
from reportes import views as reportes
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from reportes.models import Reporte
from residuos.models import RegistroResiduo
from django.http import JsonResponse
from .models import LogroUsuario
from .forms import LoginForm, RegistroForm
from itertools import groupby

class RegistroView(View):
    """
    Registro de nuevos ciudadanos.
    GET  → muestra el formulario vacío.
    POST → valida, crea el usuario y hace login automático.
    """

    template_name = 'usuarios/registro.html'
    # Si el usuario ya está autenticado, no tiene sentido que vea el registro
    redirect_authenticated_url = '/admin/'  # ajustar cuando exista la app reportes

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.redirect_authenticated_url)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = RegistroForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Login automático tras el registro — mejor UX
            login(request, user)
            messages.success(
                request,
                f'¡Bienvenido/a, {user.first_name or user.email}! Tu cuenta ha sido creada.'
            )
            # Redirigir a la página solicitada originalmente (si venía de @login_required)
            next_url = request.GET.get('next', self._default_redirect(user))
            return redirect(next_url)

        # Formulario inválido: renderiza de nuevo con errores
        return render(request, self.template_name, {'form': form})

    def _default_redirect(self, user):
        """Redirige según el rol después del registro."""
        if user.es_operador() or user.es_admin():
            return '/panel/'        # ajustar cuando exista la app panel
        return '/reportes/nuevo/'  # ajustar cuando exista la app reportes


class LoginView(View):
    """
    Login por email + contraseña.
    GET  → muestra el formulario.
    POST → autentica y redirige según rol.
    """

    template_name = 'usuarios/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self._default_redirect(request.user))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            recordarme = form.cleaned_data.get('recordarme', False)

            user = authenticate(request, username=email, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
                    return render(request, self.template_name, {'form': form})

                login(request, user)

                # Si NO marcó "recordarme", la sesión expira al cerrar el navegador
                if not recordarme:
                    request.session.set_expiry(0)

                messages.success(request, f'¡Hola de nuevo, {user.first_name or user.email}!')
                next_url = request.GET.get('next', self._default_redirect(user))
                return redirect(next_url)

            else:
                # Mensaje genérico: no revelar si el email existe o no (seguridad)
                messages.error(request, 'Correo electrónico o contraseña incorrectos.')

        return render(request, self.template_name, {'form': form})

    def _default_redirect(self, user):
        """Redirige al destino correcto según el rol del usuario."""
        if user.es_admin():
            return '/admin/'        
        elif user.es_operador():
            return '/panel/'        
        return '/reportes/nuevo/'  # ajustar cuando exista la app reportes


@login_required
def logout_view(request):
    """
    Cierra la sesión solo por POST (protección CSRF).
    GET → redirige sin cerrar sesión.
    """
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('landing')  # ajustar cuando exista la landing page

@login_required
def mi_impacto(request):
    usuario = request.user

    # ── Métricas de reportes ──────────────────────────────────
    mis_reportes = Reporte.objects.filter(usuario=usuario)

    total_reportes   = mis_reportes.count()
    reportes_resueltos = mis_reportes.filter(estado='resuelto').count()
    reportes_pendientes = mis_reportes.filter(estado='pendiente').count()
    reportes_en_gestion = mis_reportes.filter(estado='en_gestion').count()

    municipios_reportados = (
        mis_reportes.values_list('municipio', flat=True)
        .distinct()
    )

    categorias_reportadas = (
        mis_reportes.values_list('categoria', flat=True)
        .distinct()
    )

    # Tendencia: reportes este mes vs mes anterior
    hoy = date.today()
    inicio_mes_actual  = hoy.replace(day=1)
    inicio_mes_anterior = (inicio_mes_actual - timedelta(days=1)).replace(day=1)

    reportes_este_mes    = mis_reportes.filter(
        created_at__date__gte=inicio_mes_actual
    ).count()
    reportes_mes_anterior = mis_reportes.filter(
        created_at__date__gte=inicio_mes_anterior,
        created_at__date__lt=inicio_mes_actual
    ).count()

    if reportes_mes_anterior > 0:
        tendencia_pct = round(
            ((reportes_este_mes - reportes_mes_anterior) / reportes_mes_anterior) * 100
        )
    else:
        tendencia_pct = None

    # ── Métricas de residuos domésticos ──────────────────────
    mis_residuos = RegistroResiduo.objects.filter(usuario=usuario)

    totales_residuos = mis_residuos.aggregate(
        organico     = Sum('organico_kg'),
        reciclable   = Sum('reciclable_kg'),
        no_reciclable= Sum('no_reciclable_kg'),
        especial     = Sum('especial_kg'),
        peligroso    = Sum('peligroso_kg'),
    )
    total_kg = sum(v or 0 for v in totales_residuos.values())

    # Promedio del municipio para comparar
    promedio_municipio = RegistroResiduo.objects.filter(
        municipio=usuario.municipio
    ).aggregate(
        promedio=Sum('organico_kg') + Sum('reciclable_kg') +
                 Sum('no_reciclable_kg') + Sum('especial_kg') + Sum('peligroso_kg')
    )

    # ── Contribución global ───────────────────────────────────
    total_global_reportes  = Reporte.objects.count()
    total_global_resueltos = Reporte.objects.filter(estado='resuelto').count()
    total_global_kg = RegistroResiduo.objects.aggregate(
        total=Sum('organico_kg') + Sum('reciclable_kg') +
              Sum('no_reciclable_kg') + Sum('especial_kg') + Sum('peligroso_kg')
    )['total'] or 0

    pct_contribucion = (
        round((total_reportes / total_global_reportes) * 100, 1)
        if total_global_reportes > 0 else 0
    )

    # ── Datos del mapa personal ───────────────────────────────
    puntos_mapa = mis_reportes.values(
        'id', 'titulo', 'latitud', 'longitud', 'categoria', 'estado', 'municipio'
    )

    # ── Insignias obtenidas ───────────────────────────────────
    from usuarios.models import LogroUsuario
    insignias_raw = (
        LogroUsuario.objects
        .filter(usuario=usuario)
        .select_related('insignia')
        .order_by('-insignia__nivel', 'fecha_obtencion')
    )

    NIVEL_LABELS = {0: 'Especiales', 1: 'Bronce', 2: 'Plata', 3: 'Oro'}
    insignias_por_nivel = [
        {
            'nivel_label': NIVEL_LABELS.get(nivel, ''),
            'logros': list(grupo),
        }
        for nivel, grupo in groupby(insignias_raw, key=lambda l: l.insignia.nivel)
    ]

    # ── Frases de misterio (pistas de próximos logros) ────────
    pistas = _generar_pistas(usuario, total_reportes, reportes_resueltos, mis_residuos)

    # ── Frase dinámica de impacto ─────────────────────────────
    if reportes_resueltos > 0:
        frase_impacto = (
            f"Gracias a ti, {reportes_resueltos} punto"
            f"{'s' if reportes_resueltos > 1 else ''} crítico"
            f"{'s' if reportes_resueltos > 1 else ''} "
            f"{'fueron solucionados' if reportes_resueltos > 1 else 'fue solucionado'} "
            f"en {usuario.municipio}."
        )
    else:
        frase_impacto = (
            "Tu primer reporte ya está en camino de hacer la diferencia en "
            f"{usuario.municipio}."
        )

    context = {
        'total_reportes':        total_reportes,
        'reportes_resueltos':    reportes_resueltos,
        'reportes_pendientes':   reportes_pendientes,
        'reportes_en_gestion':   reportes_en_gestion,
        'reportes_este_mes':     reportes_este_mes,
        'tendencia_pct':         tendencia_pct,
        'municipios_reportados': list(municipios_reportados),
        'categorias_reportadas': list(categorias_reportadas),
        'totales_residuos':      totales_residuos,
        'total_kg':              round(total_kg, 2),
        'total_global_reportes': total_global_reportes,
        'total_global_resueltos':total_global_resueltos,
        'total_global_kg':       round(total_global_kg, 2),
        'pct_contribucion':      pct_contribucion,
        'puntos_mapa_json':      list(puntos_mapa),
        'insignias_obtenidas':   insignias_raw,
        'insignias_por_nivel':   insignias_por_nivel,
        'pistas':                pistas,
        'frase_impacto':         frase_impacto,
    }
    return render(request, 'usuarios/mi_impacto.html', context)


def _generar_pistas(usuario, total_reportes, reportes_resueltos, mis_residuos):
    """Genera pistas vagas hacia el próximo logro sin revelar las condiciones exactas."""
    pistas = []

    UMBRALES_REPORTE = [1, 5, 15, 30]
    for umbral in UMBRALES_REPORTE:
        if total_reportes < umbral:
            faltan = umbral - total_reportes
            pistas.append(
                f"Realiza {faltan} reporte{'s' if faltan > 1 else ''} más "
                "y algo especial sucederá…"
            )
            break

    UMBRALES_RESUELTOS = [1, 3, 10]
    for umbral in UMBRALES_RESUELTOS:
        if reportes_resueltos < umbral:
            pistas.append(
                "¿Puedes lograr que más de tus reportes sean resueltos? "
                "El destino guarda sorpresas para quienes persisten."
            )
            break

    semanas = mis_residuos.count()
    if semanas < 4:
        pistas.append(
            "¿Puedes mantener tu registro de residuos durante 4 semanas seguidas? "
            "El destino te observa."
        )

    return pistas[:2]  # mostrar máximo 2 pistas a la vez

@login_required
def insignias_pendientes(request):
    """
    Devuelve las insignias recién obtenidas que aún no fueron notificadas
    y las marca como notificadas.
    """
    pendientes = LogroUsuario.objects.filter(
        usuario=request.user,
        notificado=False
    ).select_related('insignia')

    datos = [
        {
            'nombre':      l.insignia.nombre,
            'descripcion': l.insignia.descripcion,
            'emoji':       l.insignia.emoji,
            'nivel':       l.insignia.nivel,
            'slug':        l.insignia.slug,
        }
        for l in pendientes
    ]

    # Marcar como notificadas
    pendientes.update(notificado=True)

    return JsonResponse({'insignias': datos})