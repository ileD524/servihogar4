"""
API Views para autenticación.
Implementa los casos de uso CU-07 (Iniciar Sesión) y CU-08 (Cerrar Sesión).
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .auth_services import AuthService
from .serializers import (
    LoginEmailSerializer,
    LoginGoogleSerializer,
    LogoutSerializer
)

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CU-07: INICIAR SESIÓN
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_email_password_api(request):
    """
    Inicia sesión con email y contraseña.
    
    **Permisos**: Acceso público (no requiere autenticación previa)
    
    **Método**: POST
    
    **URL**: /api/auth/login/
    
    **Body**:
    ```json
    {
        "email": "usuario@ejemplo.com",
        "password": "MiPassword123!"
    }
    ```
    
    **Respuestas**:
    - 200: Login exitoso - Retorna usuario y tokens JWT
    - 400: Datos inválidos o credenciales incorrectas
    - 403: Usuario bloqueado por intentos fallidos
    - 500: Error interno del servidor
    
    **Ejemplo de Respuesta Exitosa**:
    ```json
    {
        "success": true,
        "message": "Inicio de sesión exitoso",
        "data": {
            "usuario": {
                "id": 5,
                "username": "juan_perez",
                "email": "juan@ejemplo.com",
                "first_name": "Juan",
                "last_name": "Pérez",
                "rol": "profesional",
                "foto_perfil": "/media/usuarios/foto.jpg"
            },
            "tokens": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            }
        }
    }
    ```
    
    **Seguridad**:
    - Rate limiting: Máximo 5 intentos fallidos
    - Bloqueo temporal: 15 minutos tras superar el límite
    - No revela qué dato es incorrecto (email o contraseña)
    - Logs de todos los intentos (exitosos y fallidos)
    """
    
    serializer = LoginEmailSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            resultado = AuthService.login_email_password(
                email=email,
                password=password,
                request=request
            )
            
            return Response(
                {
                    'success': True,
                    'message': resultado['mensaje'],
                    'data': {
                        'usuario': resultado['usuario'],
                        'tokens': resultado['tokens']
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            # Error de validación (credenciales inválidas, usuario bloqueado, etc.)
            error_message = str(e)
            
            # Determinar código de estado según el error
            if 'bloqueado' in error_message.lower() or 'intentos' in error_message.lower():
                status_code = status.HTTP_403_FORBIDDEN
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            return Response(
                {
                    'success': False,
                    'error': error_message
                },
                status=status_code
            )
            
        except Exception as e:
            logger.error(f"Error inesperado en login: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al procesar el inicio de sesión'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(
        {
            'success': False,
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_google_api(request):
    """
    Inicia sesión con Google OAuth.
    
    **Permisos**: Acceso público (no requiere autenticación previa)
    
    **Método**: POST
    
    **URL**: /api/auth/login/google/
    
    **Body**:
    ```json
    {
        "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcifQ..."
    }
    ```
    
    **Respuestas**:
    - 200: Login exitoso - Retorna usuario y tokens JWT
    - 400: Token inválido, expirado o usuario no registrado
    - 403: Usuario desactivado
    - 500: Error interno del servidor
    
    **Ejemplo de Respuesta Exitosa**:
    ```json
    {
        "success": true,
        "message": "Inicio de sesión exitoso con Google",
        "data": {
            "usuario": {
                "id": 8,
                "username": "maria_garcia",
                "email": "maria@gmail.com",
                "first_name": "María",
                "last_name": "García",
                "rol": "cliente",
                "foto_perfil": "https://lh3.googleusercontent.com/..."
            },
            "tokens": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            }
        }
    }
    ```
    
    **Flujo**:
    1. Frontend obtiene token de Google OAuth
    2. Frontend envía token al backend
    3. Backend valida token con Google API
    4. Backend busca o vincula usuario
    5. Backend genera tokens JWT propios
    6. Frontend usa tokens JWT para requests subsecuentes
    
    **Seguridad**:
    - Valida token directamente con Google API
    - Verifica que el email esté verificado en Google
    - No permite login si el usuario no está registrado
    - Logs de todos los accesos
    """
    
    serializer = LoginGoogleSerializer(data=request.data)
    
    if serializer.is_valid():
        google_token = serializer.validated_data['token']
        
        try:
            resultado = AuthService.login_google(
                google_token=google_token,
                request=request
            )
            
            return Response(
                {
                    'success': True,
                    'message': resultado['mensaje'],
                    'data': {
                        'usuario': resultado['usuario'],
                        'tokens': resultado['tokens']
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            # Error de validación
            error_message = str(e)
            
            # Determinar código de estado
            if 'desactivad' in error_message.lower():
                status_code = status.HTTP_403_FORBIDDEN
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            return Response(
                {
                    'success': False,
                    'error': error_message
                },
                status=status_code
            )
            
        except Exception as e:
            logger.error(f"Error inesperado en login Google: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al procesar el inicio de sesión con Google'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(
        {
            'success': False,
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


# ============================================================================
# CU-08: CERRAR SESIÓN
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Cierra la sesión del usuario autenticado.
    
    **Permisos**: Usuario autenticado (cualquier rol)
    
    **Método**: POST
    
    **URL**: /api/auth/logout/
    
    **Headers**:
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Body** (opcional):
    ```json
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    ```
    
    **Respuestas**:
    - 200: Logout exitoso
    - 400: Error al cerrar sesión
    - 401: No autenticado
    - 500: Error interno del servidor
    
    **Ejemplo de Respuesta Exitosa**:
    ```json
    {
        "success": true,
        "message": "Sesión cerrada exitosamente"
    }
    ```
    
    **Proceso**:
    1. Guarda automáticamente datos de sesión (Django)
    2. Invalida refresh token si se proporciona (blacklist)
    3. Destruye sesión de Django
    4. Registra logout en logs
    
    **Nota**: 
    - Tras el logout, el access token actual seguirá siendo válido hasta su expiración natural (generalmente 5-15 minutos)
    - El refresh token se invalida inmediatamente si se proporciona
    - Para invalidación inmediata del access token, implementar blacklist en el middleware
    """
    
    serializer = LogoutSerializer(data=request.data)
    
    if serializer.is_valid():
        refresh_token = serializer.validated_data.get('refresh_token')
        
        try:
            resultado = AuthService.logout_user(
                usuario=request.user,
                refresh_token=refresh_token,
                request=request
            )
            
            return Response(
                {
                    'success': True,
                    'message': resultado['mensaje']
                },
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            logger.warning(f"Error en logout para usuario {request.user.id}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Error inesperado en logout: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al cerrar la sesión'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(
        {
            'success': False,
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


# ============================================================================
# ENDPOINTS AUXILIARES
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verificar_sesion_api(request):
    """
    Verifica si el usuario tiene una sesión activa válida.
    
    **Permisos**: Usuario autenticado
    
    **Método**: GET
    
    **URL**: /api/auth/verificar-sesion/
    
    **Headers**:
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Respuestas**:
    - 200: Sesión válida - Retorna info del usuario
    - 401: Token inválido o expirado
    
    **Ejemplo de Respuesta**:
    ```json
    {
        "success": true,
        "data": {
            "autenticado": true,
            "usuario": {
                "id": 5,
                "username": "juan_perez",
                "email": "juan@ejemplo.com",
                "first_name": "Juan",
                "last_name": "Pérez",
                "rol": "profesional"
            }
        }
    }
    ```
    
    **Uso**: 
    - Frontend puede llamar a este endpoint al cargar la aplicación
    - Verifica si el token almacenado sigue siendo válido
    - Obtiene información actualizada del usuario
    """
    
    usuario = request.user
    rol = AuthService._get_user_role(usuario)
    
    return Response(
        {
            'success': True,
            'data': {
                'autenticado': True,
                'usuario': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'email': usuario.email,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'rol': rol,
                    'foto_perfil': usuario.foto_perfil.url if usuario.foto_perfil else None
                }
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_api(request):
    """
    Refresca el access token usando el refresh token.
    
    **Permisos**: Acceso público
    
    **Método**: POST
    
    **URL**: /api/auth/refresh/
    
    **Body**:
    ```json
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    ```
    
    **Respuestas**:
    - 200: Token refrescado exitosamente
    - 400: Refresh token inválido o en blacklist
    - 500: Error interno
    
    **Ejemplo de Respuesta**:
    ```json
    {
        "success": true,
        "data": {
            "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    }
    ```
    
    **Nota**: Este endpoint usa la funcionalidad de djangorestframework-simplejwt
    """
    
    from rest_framework_simplejwt.views import TokenRefreshView
    from rest_framework_simplejwt.serializers import TokenRefreshSerializer
    
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {
                'success': False,
                'error': 'Refresh token requerido'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar si está en blacklist
    if AuthService.is_token_blacklisted(refresh_token):
        return Response(
            {
                'success': False,
                'error': 'Token inválido o expirado'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        serializer.is_valid(raise_exception=True)
        
        return Response(
            {
                'success': True,
                'data': {
                    'access': serializer.validated_data['access']
                }
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.warning(f"Error al refrescar token: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'Token inválido o expirado'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
