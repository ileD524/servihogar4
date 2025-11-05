"""
URLs para la API REST de usuarios.
Define los endpoints para los casos de uso CU-01, CU-02, CU-03, CU-04, CU-05 y CU-06.
"""
from django.urls import path
from . import api_views, admin_api_views

app_name = 'usuarios_api'

urlpatterns = [
    # ========================================================================
    # CU-01: REGISTRAR PERFIL
    # ========================================================================
    
    # Registro manual
    path('registrar/', 
         api_views.registrar_usuario_api, 
         name='registrar_usuario'),
    
    # Registro con Google
    path('registrar/google/', 
         api_views.registrar_usuario_google_api, 
         name='registrar_google'),
    
    # Completar datos de usuario registrado con Google
    path('completar-datos/', 
         api_views.completar_datos_google_api, 
         name='completar_datos_google'),
    
    # Confirmar email
    path('confirmar/<str:uidb64>/<str:token>/', 
         api_views.confirmar_email_api, 
         name='confirmar_email'),
    
    # ========================================================================
    # CU-03: MODIFICAR PERFIL
    # ========================================================================
    
    # Obtener perfil del usuario autenticado
    path('perfil/', 
         api_views.obtener_perfil_api, 
         name='obtener_perfil'),
    
    # Modificar perfil del usuario autenticado
    path('perfil/modificar/', 
         api_views.modificar_perfil_api, 
         name='modificar_perfil'),
    
    # ========================================================================
    # CU-02: ELIMINAR PERFIL
    # ========================================================================
    
    # Eliminar perfil del usuario autenticado
    path('perfil/eliminar/', 
         api_views.eliminar_perfil_api, 
         name='eliminar_perfil'),
    
    # Verificar si puede eliminar perfil
    path('perfil/puede-eliminar/', 
         api_views.verificar_puede_eliminar_api, 
         name='verificar_puede_eliminar'),
    
    # ========================================================================
    # CU-04, CU-05, CU-06: GESTIÓN ADMINISTRATIVA DE USUARIOS
    # ========================================================================
    
    # Listar usuarios (con filtros, búsqueda y paginación)
    path('admin/', 
         admin_api_views.listar_usuarios_api, 
         name='admin_listar_usuarios'),
    
    # Registrar usuario por administrador (CU-04)
    path('admin/registrar/', 
         admin_api_views.registrar_usuario_admin_api, 
         name='admin_registrar_usuario'),
    
    # Obtener detalle de un usuario
    path('admin/<int:usuario_id>/', 
         admin_api_views.obtener_usuario_api, 
         name='admin_obtener_usuario'),
    
    # Modificar usuario por administrador (CU-05)
    path('admin/<int:usuario_id>/modificar/', 
         admin_api_views.modificar_usuario_admin_api, 
         name='admin_modificar_usuario'),
    
    # Eliminar usuario por administrador (CU-06)
    path('admin/<int:usuario_id>/eliminar/', 
         admin_api_views.eliminar_usuario_admin_api, 
         name='admin_eliminar_usuario'),
]
