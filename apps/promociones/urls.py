from django.urls import path
from . import views

app_name = 'promociones'

urlpatterns = [
    # Gestión de Servicios
    path('', views.buscar_promocion, name='buscar_promocion'),  # CU-45: Buscar Promoción
    path('registrar/', views.registrar_promocion, name='registrar_promocion'),  # CU-18
    path('modificar/<int:id>/', views.modificar_promocion, name='modificar_promocion'),  # CU-19
    path('eliminar/<int:id>/', views.eliminar_promocion, name='eliminar_promocion'),  # CU-20

    
    # Vistas AJAX para modales
    path('registrar/ajax/', views.registrar_promocion_ajax, name='registrar_promocion_ajax'),
    path('api/promocion/<int:id>/', views.obtener_promocion_ajax, name='obtener_promocion_ajax'),
    path('ver/<int:id>/ajax/', views.ver_promocion_ajax, name='ver_promocion_ajax'),
    path('modificar/<int:id>/ajax/', views.modificar_promocion_ajax, name='modificar_promocion_ajax'),
    path('eliminar/<int:id>/ajax/', views.eliminar_promocion_ajax, name='eliminar_promocion_ajax'),
    path('activar/<int:id>/ajax/', views.activar_promocion_ajax, name='activar_promocion_ajax'),
]

