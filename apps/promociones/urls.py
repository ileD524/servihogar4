from django.urls import path
from . import views

app_name = 'promociones'

urlpatterns = [
    # CU-18: Registrar Promoción
    path('registrar/', views.registrar_promocion, name='registrar_promocion'),
    
    # CU-19: Modificar Promoción
    path('modificar/<int:id>/', views.modificar_promocion, name='modificar_promocion'),
    
    # CU-20: Eliminar Promoción
    path('eliminar/<int:id>/', views.eliminar_promocion, name='eliminar_promocion'),
    
    # CU-45: Buscar Promoción
    path('buscar/', views.buscar_promocion, name='buscar_promocion'),
    
    # Vistas adicionales
    path('ver/<int:id>/', views.ver_promocion, name='ver_promocion'),
    path('listar/', views.listar_promociones, name='listar_promociones'),
    path('vigentes/', views.promociones_vigentes, name='promociones_vigentes'),
    
    # Vistas AJAX para modales
    path('ver/<int:id>/ajax/', views.ver_promocion_ajax, name='ver_promocion_ajax'),
    path('modificar/<int:id>/ajax/', views.modificar_promocion_ajax, name='modificar_promocion_ajax'),
    path('eliminar/<int:id>/ajax/', views.eliminar_promocion_ajax, name='eliminar_promocion_ajax'),
]
