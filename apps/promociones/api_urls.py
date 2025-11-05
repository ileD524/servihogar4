"""
URLs de la API REST para Promociones
"""
from django.urls import path
from .api_views import (
    PromocionListCreateAPIView,
    PromocionDetailAPIView,
    PromocionValidarEliminacionAPIView,
    PromocionVigentesAPIView
)

app_name = 'promociones_api'

urlpatterns = [
    # CU-18: Registrar Promoción (POST)
    # Lista de promociones (GET)
    path('', PromocionListCreateAPIView.as_view(), name='promocion-list-create'),
    
    # Promociones vigentes (público)
    path('vigentes/', PromocionVigentesAPIView.as_view(), name='promocion-vigentes'),
    
    # CU-19: Modificar Promoción (PUT)
    # CU-20: Eliminar Promoción (DELETE)
    # Detalle de promoción (GET)
    path('<int:id>/', PromocionDetailAPIView.as_view(), name='promocion-detail'),
    
    # Validar si puede eliminarse una promoción
    path('<int:id>/validar-eliminacion/', PromocionValidarEliminacionAPIView.as_view(), name='promocion-validar-eliminacion'),
]
