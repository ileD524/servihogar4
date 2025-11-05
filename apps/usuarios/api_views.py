"""
Vistas API REST para gestión de perfiles de usuario.
Implementa los casos de uso CU-01, CU-02 y CU-03 como endpoints REST.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.exceptions import ValidationError
import logging

from .models import Usuario
from .services import UsuarioService
from .serializers import (
    UsuarioSerializer,
    RegistroUsuarioSerializer,
    ModificarPerfilSerializer,
    GoogleAuthSerializer,
    CompletarDatosGoogleSerializer,
    ConfirmarEmailSerializer,
    EliminarPerfilSerializer
)

logger = logging.getLogger(__name__)


# ============================================================================
# CU-01: REGISTRAR PERFIL
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_usuario_api(request):
    """
    CU-01: Registrar nuevo usuario (cliente o profesional).
    
    POST /api/usuarios/registrar/
    
    Body (application/json):
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "password_confirm": "string",
        "first_name": "string",
        "last_name": "string",
        "telefono": "string" (opcional),
        "direccion": "string" (opcional),
        "rol": "cliente" | "profesional",
        
        // Solo para profesionales:
        "anios_experiencia": integer (opcional),
        "servicios": [id1, id2, ...] (requerido para profesionales),
        "horarios": [
            {
                "dia": "lunes" | "martes" | ...,
                "hora_inicio": "HH:MM",
                "hora_fin": "HH:MM"
            }
        ] (requerido para profesionales)
    }
    
    Responses:
        201: Usuario registrado exitosamente. Email de confirmación enviado.
        400: Errores de validación
    """
    serializer = RegistroUsuarioSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Preparar datos para el servicio
        datos_usuario = {
            'username': serializer.validated_data['username'],
            'email': serializer.validated_data['email'],
            'password': serializer.validated_data['password'],
            'first_name': serializer.validated_data['first_name'],
            'last_name': serializer.validated_data['last_name'],
            'telefono': serializer.validated_data.get('telefono', ''),
            'direccion': serializer.validated_data.get('direccion', ''),
            'rol': serializer.validated_data['rol'],
        }
        
        datos_perfil = None
        if serializer.validated_data['rol'] == 'profesional':
            datos_perfil = {
                'anios_experiencia': serializer.validated_data.get('anios_experiencia', 0),
                'servicios': serializer.validated_data.get('servicios', []),
                'horarios': serializer.validated_data.get('horarios', []),
            }
        
        # Registrar usuario usando el servicio
        usuario, errores = UsuarioService.registrar_usuario_manual(
            datos_usuario, 
            datos_perfil, 
            request
        )
        
        if errores:
            return Response({
                'success': False,
                'errors': errores
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Serializar usuario creado
        usuario_serializado = UsuarioSerializer(usuario)
        
        return Response({
            'success': True,
            'message': 'Usuario registrado exitosamente. Por favor revisa tu email para confirmar tu cuenta.',
            'usuario': usuario_serializado.data
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': e.messages if hasattr(e, 'messages') else [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error en registrar_usuario_api: {str(e)}")
        return Response({
            'success': False,
            'errors': ['Error interno del servidor']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_usuario_google_api(request):
    """
    CU-01: Registrar usuario con autenticación Google.
    
    POST /api/usuarios/registrar/google/
    
    Body (application/json):
    {
        "code": "código de autorización de Google"
    }
    
    Nota: En un flujo real, este endpoint intercambiaría el código por
    un access token y obtendría los datos del usuario de Google.
    Para simplificar, este ejemplo asume que los datos vienen en el request.
    
    Responses:
        201: Usuario registrado/autenticado con Google
        400: Errores de validación
    """
    serializer = GoogleAuthSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # En implementación real, aquí se intercambiaría el código por token
        # y se obtendrían los datos del usuario de Google
        # Por ahora, asumimos que vienen en el request
        google_data = {
            'google_id': request.data.get('google_id'),
            'email': request.data.get('email'),
            'first_name': request.data.get('first_name', ''),
            'last_name': request.data.get('last_name', ''),
        }
        
        usuario = UsuarioService.registrar_usuario_google(google_data)
        usuario_serializado = UsuarioSerializer(usuario)
        
        return Response({
            'success': True,
            'message': 'Autenticación con Google exitosa',
            'usuario': usuario_serializado.data,
            'datos_completos': bool(usuario.telefono and usuario.direccion)
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': e.messages if hasattr(e, 'messages') else [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error en registrar_usuario_google_api: {str(e)}")
        return Response({
            'success': False,
            'errors': ['Error interno del servidor']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def completar_datos_google_api(request):
    """
    CU-01: Completar datos de usuario registrado con Google.
    
    PUT/PATCH /api/usuarios/completar-datos/
    
    Body (application/json):
    {
        "telefono": "string" (opcional),
        "direccion": "string" (opcional),
        "rol": "cliente" | "profesional" (opcional),
        
        // Si cambia a profesional:
        "anios_experiencia": integer,
        "servicios": [id1, id2, ...],
        "horarios": [{"dia": "...", "hora_inicio": "...", "hora_fin": "..."}]
    }
    
    Responses:
        200: Datos actualizados exitosamente
        400: Errores de validación
        403: Usuario no registrado con Google
    """
    usuario = request.user
    
    # Validar que sea usuario de Google
    if not usuario.google_id:
        return Response({
            'success': False,
            'errors': ['Este endpoint es solo para usuarios registrados con Google']
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CompletarDatosGoogleSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        datos_adicionales = dict(serializer.validated_data)
        
        # Si cambia a profesional, preparar datos_perfil
        if 'rol' in datos_adicionales and datos_adicionales['rol'] == 'profesional':
            datos_adicionales['datos_perfil'] = {
                'anios_experiencia': datos_adicionales.pop('anios_experiencia', 0),
                'servicios': datos_adicionales.pop('servicios', []),
                'horarios': datos_adicionales.pop('horarios', []),
            }
        
        usuario_actualizado = UsuarioService.completar_datos_usuario_google(
            usuario.id,
            datos_adicionales
        )
        
        usuario_serializado = UsuarioSerializer(usuario_actualizado)
        
        return Response({
            'success': True,
            'message': 'Datos completados exitosamente',
            'usuario': usuario_serializado.data
        }, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': e.messages if hasattr(e, 'messages') else [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error en completar_datos_google_api: {str(e)}")
        return Response({
            'success': False,
            'errors': ['Error interno del servidor']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def confirmar_email_api(request, uidb64, token):
    """
    CU-01: Confirmar email de usuario.
    
    GET /api/usuarios/confirmar/<uidb64>/<token>/
    
    Responses:
        200: Email confirmado exitosamente
        400: Token inválido o expirado
    """
    try:
        # Decodificar UID
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.objects.get(pk=uid)
        
        # Validar token
        if not default_token_generator.check_token(usuario, token):
            return Response({
                'success': False,
                'errors': ['El enlace de confirmación es inválido o ha expirado']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Confirmar email
        usuario_confirmado = UsuarioService.confirmar_email(usuario.id)
        usuario_serializado = UsuarioSerializer(usuario_confirmado)
        
        return Response({
            'success': True,
            'message': '¡Email confirmado exitosamente! Ya puedes iniciar sesión.',
            'usuario': usuario_serializado.data
        }, status=status.HTTP_200_OK)
        
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        return Response({
            'success': False,
            'errors': ['El enlace de confirmación es inválido']
        }, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': e.messages if hasattr(e, 'messages') else [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error en confirmar_email_api: {str(e)}")
        return Response({
            'success': False,
            'errors': ['Error interno del servidor']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# CU-03: MODIFICAR PERFIL
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_perfil_api(request):
    """
    CU-03: Obtener datos del perfil del usuario autenticado.
    
    GET /api/usuarios/perfil/
    
    Responses:
        200: Datos del perfil
    """
    usuario = request.user
    serializer = UsuarioSerializer(usuario)
    
    return Response({
        'success': True,
        'usuario': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def modificar_perfil_api(request):
    """
    CU-03: Modificar perfil del usuario autenticado.
    
    PUT/PATCH /api/usuarios/perfil/
    
    Body (application/json):
    {
        "first_name": "string" (opcional),
        "last_name": "string" (opcional),
        "email": "string" (opcional),
        "telefono": "string" (opcional),
        "direccion": "string" (opcional),
        "foto_perfil": file (opcional),
        
        // Para profesionales:
        "anios_experiencia": integer (opcional),
        "servicios": [id1, id2, ...] (opcional),
        "horarios": [{"dia": "...", "hora_inicio": "...", "hora_fin": "..."}] (opcional)
    }
    
    Responses:
        200: Perfil modificado exitosamente
        400: Errores de validación
    """
    usuario = request.user
    serializer = ModificarPerfilSerializer(
        data=request.data,
        context={'usuario': usuario}
    )
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        datos_actualizados = {}
        datos_perfil = None
        
        # Separar datos básicos de datos de perfil
        for key, value in serializer.validated_data.items():
            if key in ['anios_experiencia', 'servicios', 'horarios']:
                if datos_perfil is None:
                    datos_perfil = {}
                datos_perfil[key] = value
            else:
                datos_actualizados[key] = value
        
        # Modificar perfil usando el servicio
        usuario_actualizado = UsuarioService.modificar_perfil(
            usuario.id,
            datos_actualizados,
            datos_perfil
        )
        
        usuario_serializado = UsuarioSerializer(usuario_actualizado)
        
        return Response({
            'success': True,
            'message': 'Perfil modificado exitosamente',
            'usuario': usuario_serializado.data
        }, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': e.messages if hasattr(e, 'messages') else [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error en modificar_perfil_api: {str(e)}")
        return Response({
            'success': False,
            'errors': ['Error interno del servidor']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# CU-02: ELIMINAR PERFIL
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def eliminar_perfil_api(request):
    """
    CU-02: Eliminar perfil del usuario autenticado.
    
    POST /api/usuarios/perfil/eliminar/
    
    Body (application/json):
    {
        "confirmar": true,
        "password": "string" (opcional, solo para usuarios con autenticación manual)
    }
    
    Validaciones:
    - No puede tener turnos activos/pendientes
    - No puede tener pagos pendientes
    - Debe confirmar explícitamente la eliminación
    
    Responses:
        200: Perfil eliminado exitosamente
        400: No cumple condiciones o errores de validación
        403: Contraseña incorrecta
    """
    usuario = request.user
    serializer = EliminarPerfilSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Validar contraseña si es usuario con autenticación manual
        if not usuario.google_id:
            password = request.data.get('password')
            if not password:
                return Response({
                    'success': False,
                    'errors': ['Debe proporcionar su contraseña para confirmar']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not usuario.check_password(password):
                return Response({
                    'success': False,
                    'errors': ['Contraseña incorrecta']
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Eliminar perfil usando el servicio
        resultado = UsuarioService.eliminar_perfil(usuario.id)
        
        return Response({
            'success': True,
            'message': resultado['mensaje'],
            'fecha_eliminacion': resultado['fecha_eliminacion']
        }, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': e.messages if hasattr(e, 'messages') else [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error en eliminar_perfil_api: {str(e)}")
        return Response({
            'success': False,
            'errors': ['Error interno del servidor']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verificar_puede_eliminar_api(request):
    """
    Verificar si el usuario autenticado puede eliminar su perfil.
    
    GET /api/usuarios/perfil/puede-eliminar/
    
    Responses:
        200: Información sobre si puede eliminar y razones
    """
    from .validators import PerfilValidator
    
    usuario = request.user
    puede_eliminar, mensaje_error = PerfilValidator.puede_eliminar_perfil(usuario)
    
    return Response({
        'success': True,
        'puede_eliminar': puede_eliminar,
        'mensaje': mensaje_error if not puede_eliminar else 'Puede eliminar su perfil'
    }, status=status.HTTP_200_OK)
