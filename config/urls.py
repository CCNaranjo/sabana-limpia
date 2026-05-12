
from django.contrib import admin
from django.urls import path, include          
from django.conf import settings               
from django.conf.urls.static import static     

urlpatterns = [
    # Panel administrativo de Django
    path('admin/', admin.site.urls),
    
    # URLs de la app usuarios (registro, login, logout)
    path('auth/', include('usuarios.urls')),
    
    # URLs de la app reportes (nuevo reporte, mis reportes, mapa)
    path('reportes/', include('reportes.urls')),        # ← incluye las rutas raíz de reportes
    
    # URLs de la app residuos (registro doméstico, estadísticas)
    path('residuos/', include('residuos.urls')),

    # Panel operador
    path('panel/', include('panel.urls')),
]

# Servir archivos multimedia (imágenes) solo en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
