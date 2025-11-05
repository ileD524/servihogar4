from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # CU-01: Registrar Usuario (cliente o profesional se auto-registra)
    path('registrar/', views.registrar_usuario, name='registrar_usuario'),
    
    # CU-07: Iniciar Sesión
    path('login/', views.iniciar_sesion, name='login'),
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
    
    # CU-08: Cerrar Sesión
    path('logout/', views.cerrar_sesion, name='logout'),
    
    # CU-03: Modificar Perfil (usuario modifica su propio perfil)
    path('perfil/modificar/', views.modificar_perfil, name='modificar_perfil'),
    
    # CU-02: Eliminar Perfil (usuario da de baja su propia cuenta)
    path('perfil/eliminar/', views.eliminar_perfil, name='eliminar_perfil'),
    
    # CU-01: Confirmar Email
    path('confirmar/<str:uidb64>/<str:token>/', views.confirmar_email, name='confirmar_email'),
    
    # Gestión de usuarios por ADMINISTRADOR
    path('admin/registrar/', views.registrar_usuario_admin, name='registrar_usuario_admin'),
    path('admin/buscar/', views.buscar_usuario, name='buscar_usuario'),
    path('modificar/<int:id>/', views.modificar_usuario, name='modificar_usuario'),
    path('eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('activar/<int:id>/', views.activar_usuario, name='activar_usuario'),
    
    # Vistas adicionales
    path('perfil/<int:id>/', views.perfil_usuario, name='perfil'),
    
    # Vistas AJAX para modales
    path('perfil/<int:id>/ajax/', views.perfil_usuario_ajax, name='perfil_ajax'),
    path('modificar/<int:id>/ajax/', views.modificar_usuario_ajax, name='modificar_usuario_ajax'),
    path('eliminar/<int:id>/ajax/', views.eliminar_usuario_ajax, name='eliminar_usuario_ajax'),
    path('activar/<int:id>/ajax/', views.activar_usuario_ajax, name='activar_usuario_ajax'),
    
    # Dashboards
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/profesional/', views.dashboard_profesional, name='dashboard_profesional'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
]
