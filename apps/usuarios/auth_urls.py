"""
URLs para la API de autenticación.
Define los endpoints para los casos de uso CU-07 y CU-08.
"""
from django.urls import path
from . import auth_api_views

app_name = 'auth_api'

urlpatterns = [
    # ========================================================================
    # CU-07: INICIAR SESIÓN
    # ========================================================================
    
    # Login con email y contraseña
    path('login/', 
         auth_api_views.login_email_password_api, 
         name='login'),
    
    # Login con Google OAuth
    path('login/google/', 
         auth_api_views.login_google_api, 
         name='login_google'),
    
    # ========================================================================
    # CU-08: CERRAR SESIÓN
    # ========================================================================
    
    # Logout
    path('logout/', 
         auth_api_views.logout_api, 
         name='logout'),
    
    # ========================================================================
    # ENDPOINTS AUXILIARES
    # ========================================================================
    
    # Verificar sesión activa
    path('verificar-sesion/', 
         auth_api_views.verificar_sesion_api, 
         name='verificar_sesion'),
    
    # Refrescar access token
    path('refresh/', 
         auth_api_views.refresh_token_api, 
         name='refresh_token'),
]
