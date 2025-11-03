from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    # Gestión de Servicios
    path('', views.buscar_servicio, name='buscar_servicio'),  # CU-39: Buscar Servicio
    path('registrar/', views.registrar_servicio, name='registrar_servicio'),  # CU-13
    path('modificar/<int:id>/', views.modificar_servicio, name='modificar_servicio'),  # CU-15
    path('eliminar/<int:id>/', views.eliminar_servicio, name='eliminar_servicio'),  # CU-14
    path('activar/<int:id>/', views.activar_servicio, name='activar_servicio'),  # Activar servicio
    
    # Gestión de Categorías
    path('categorias/', views.buscar_categoria, name='buscar_categoria'),  # CU-40
    path('categorias/<int:id>/', views.ver_categoria, name='ver_categoria'),  # Ver detalles de categoría
    path('categorias/registrar/', views.registrar_categoria, name='registrar_categoria'),  # CU-36
    path('categorias/modificar/<int:id>/', views.modificar_categoria, name='modificar_categoria'),  # CU-37
    path('categorias/eliminar/<int:id>/', views.eliminar_categoria, name='eliminar_categoria'),  # CU-38
    path('categorias/toggle/<int:id>/', views.toggle_categoria, name='toggle_categoria'),  # Activar/Desactivar
]
