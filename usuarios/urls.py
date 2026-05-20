from django.urls import path

from . import views

app_name = 'usuarios'  # Namespace para reverse() y {% url %} en templates

urlpatterns = [
    path('registro/',  views.RegistroView.as_view(), name='registro'),
    path('login/',     views.LoginView.as_view(),    name='login'),
    path('logout/',    views.logout_view,            name='logout'),
    path('mi-impacto/',views.mi_impacto,             name='mi_impacto'),
    path('api/insignias-pendientes/', views.insignias_pendientes, name='insignias_pendientes'),
]