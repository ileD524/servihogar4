"""
URLs de la API REST para Reportes, Estadísticas y Búsqueda
"""
from django.urls import path
from .api_views import (
    EstadisticasAPIView,
    ReporteClientesAPIView,
    ReporteProfesionalesAPIView,
    PromocionBusquedaAPIView,
    PromocionDetalleAPIView,
    ReportesListAPIView,
    ReporteDetalleAPIView
)

app_name = 'reportes_api'

urlpatterns = [
    # CU-16: Consultar Estadísticas
    path('estadisticas/', EstadisticasAPIView.as_view(), name='estadisticas'),
    
    # CU-31: Reporte de Preferencias de Clientes
    path('clientes/', ReporteClientesAPIView.as_view(), name='reporte-clientes'),
    
    # CU-30: Reporte de Profesionales
    path('profesionales/', ReporteProfesionalesAPIView.as_view(), name='reporte-profesionales'),
    
    # CU-40: Búsqueda de Promociones
    path('promociones/buscar/', PromocionBusquedaAPIView.as_view(), name='promociones-buscar'),
    path('promociones/<int:id>/detalle/', PromocionDetalleAPIView.as_view(), name='promociones-detalle'),
    
    # Gestión de Reportes Guardados
    path('', ReportesListAPIView.as_view(), name='reportes-list'),
    path('<int:id>/', ReporteDetalleAPIView.as_view(), name='reporte-detalle'),
]
