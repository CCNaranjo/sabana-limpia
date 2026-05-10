"""
usuarios/decorators.py
======================
Decoradores de autorización para SabanaLimpia.

Uso:
    from usuarios.decorators import rol_requerido

    @login_required                    # de Django — verifica sesión activa
    @rol_requerido('operador')         # verifica el rol
    def mi_vista(request):
        ...

    # También acepta múltiples roles permitidos:
    @login_required
    @rol_requerido('operador', 'admin')
    def vista_mixta(request):
        ...
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def rol_requerido(*roles_permitidos):
    """
    Decorador de autorización por rol.

    Parámetros:
        *roles_permitidos: uno o más valores de CustomUser.Rol
                           ej: 'ciudadano', 'operador', 'admin'

    Comportamiento:
        - Si el usuario NO está autenticado → redirige a /auth/login/
          (esto es respaldo; lo normal es combinar con @login_required antes)
        - Si el usuario está autenticado pero su rol no está en los permitidos
          → redirige a home (/) con mensaje de advertencia.
        - Si el usuario tiene el rol correcto → ejecuta la vista normalmente.

    Ejemplo:
        @login_required
        @rol_requerido('operador')
        def panel_operador(request):
            ...

        @login_required
        @rol_requerido('operador', 'admin')
        def vista_compartida(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)  # preserva __name__, __doc__, etc. de la vista original
        def wrapper(request, *args, **kwargs):

            # Respaldo: si llega sin sesión (no usaron @login_required antes)
            if not request.user.is_authenticated:
                messages.warning(
                    request,
                    'Debes iniciar sesión para acceder a esta página.'
                )
                return redirect('usuarios:login')

            # Verificación de rol
            if request.user.rol not in roles_permitidos:
                messages.warning(
                    request,
                    'No tienes permiso para acceder a esta sección.'
                )
                return redirect('landing')  # → home pública

            # Todo ok: ejecutar la vista
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator