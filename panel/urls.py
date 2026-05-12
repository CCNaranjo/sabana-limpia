from django.urls import path
from . import views

app_name = 'panel'

urlpatterns = [
    path('', views.ListaReportesView.as_view(), name='lista'),
    path('reporte/<int:pk>/', views.DetalleReporteView.as_view(), name='detalle'),
]