from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views import View

from .forms import LoginForm, RegistroForm


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
            return '/admin/'        # ajustar cuando exista la app panel
        return '/admin/login/'  # ajustar cuando exista la app reportes


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
        if user.es_operador() or user.es_admin():
            return '/admin/'        # ajustar cuando exista la app panel
        return '/admin/'  # ajustar cuando exista la app reportes


@login_required
def logout_view(request):
    """
    Cierra la sesión solo por POST (protección CSRF).
    GET → redirige sin cerrar sesión.
    """
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('/auth/login/')  # ajustar cuando exista la landing page