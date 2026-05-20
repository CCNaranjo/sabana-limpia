from django.conf import settings

def tawk_settings(request):
    """Pasa las credenciales de Tawk.to a todos los templates."""
    return {
        'TAWK_PROPERTY_ID': settings.TAWK_PROPERTY_ID,
        'TAWK_WIDGET_ID':   settings.TAWK_WIDGET_ID,
    }