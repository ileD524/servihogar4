"""
API Views para la gestión administrativa de usuarios.
Implementa los casos de uso CU-04, CU-05, CU-06.

Solo accesible para administradores.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage

from .admin_services import AdminUsuarioService
from .serializers import (
    AdminRegistroUsuarioSerializer,
    AdminModificarUsuarioSerializer,
    AdminEliminarUsuarioSerializer,
    FiltrosUsuarioSerializer
)

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CU-04: REGISTRAR USUARIO (ADMINISTRADOR)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAdminUser])
def registrar_usuario_admin_api(request):
    """
    Registra un nuevo usuario (cliente o profesional) por parte del administrador.
    
    El administrador puede:
    - Crear usuarios directamente activos o en estado pendiente
    - Asignar rol (cliente/profesional)
    - Crear con autenticación manual o Google
    - Si no se proporciona contraseña, se genera una temporal
    
    **Permisos**: Solo administradores
    
    **Método**: POST
    
    **URL**: /api/admin/usuarios/registrar/
    
    **Body**:
    ```json
    {
        "username": "nuevo_usuario",
        "email": "usuario@ejemplo.com",
        "password": "opcional",
        "first_name": "Nombre",
        "last_name": "Apellido",
        "telefono": "opcional",
        "direccion": "opcional",
        "rol": "cliente|profesional",
        "estado": "activo|pendiente",
        "google_id": "opcional",
        "anios_experiencia": 0,
        "servicios": [1, 2, 3],
        "horarios": [{"dia": "lunes", "hora_inicio": "09:00", "hora_fin": "18:00"}]
    }
    ```
    
    **Respuestas**:
    - 201: Usuario creado exitosamente
    - 400: Error de validación
    - 403: No tiene permisos de administrador
    """
    serializer = AdminRegistroUsuarioSerializer(data=request.data)
    
    if serializer.is_valid():
        datos_validados = serializer.validated_data
        
        try:
            # Obtener el administrador que está creando el usuario
            admin_usuario = request.user
            
            resultado = AdminUsuarioService.registrar_usuario_admin(
                datos_usuario=datos_validados,
                admin_usuario=admin_usuario
            )
            
            return Response(
                {
                    'success': True,
                    'message': 'Usuario registrado exitosamente',
                    'data': {
                        'usuario_id': resultado['usuario'].id,
                        'username': resultado['usuario'].username,
                        'email': resultado['usuario'].email,
                        'rol': resultado['rol'],
                        'estado': 'activo' if resultado['usuario'].is_active else 'pendiente',
                        'requiere_confirmacion': resultado.get('requiere_confirmacion', False)
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            logger.warning(f"Error de validación al registrar usuario (admin): {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado al registrar usuario (admin): {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al procesar la solicitud'
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
# CU-05: MODIFICAR USUARIO (ADMINISTRADOR)
# ============================================================================

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def modificar_usuario_admin_api(request, usuario_id):
    """
    Modifica los datos de cualquier usuario por parte del administrador.
    
    El administrador puede:
    - Modificar cualquier campo del usuario
    - Cambiar el rol (con validaciones)
    - Activar/desactivar usuarios
    - NO puede modificar otros administradores
    
    **Permisos**: Solo administradores
    
    **Método**: PUT/PATCH
    
    **URL**: /api/admin/usuarios/<id>/modificar/
    
    **Parámetros URL**:
    - usuario_id: ID del usuario a modificar
    
    **Body** (todos los campos son opcionales):
    ```json
    {
        "username": "nuevo_username",
        "email": "nuevo@email.com",
        "first_name": "Nuevo Nombre",
        "last_name": "Nuevo Apellido",
        "telefono": "123456789",
        "direccion": "Nueva dirección",
        "rol": "cliente|profesional",
        "activo": true,
        "anios_experiencia": 5,
        "servicios": [1, 2],
        "horarios": [...]
    }
    ```
    
    **Respuestas**:
    - 200: Usuario modificado exitosamente
    - 400: Error de validación
    - 403: No tiene permisos o intenta modificar otro admin
    - 404: Usuario no encontrado
    """
    serializer = AdminModificarUsuarioSerializer(
        data=request.data,
        context={'usuario_id': usuario_id}
    )
    
    if serializer.is_valid():
        datos_actualizados = serializer.validated_data
        
        try:
            admin_usuario = request.user
            
            resultado = AdminUsuarioService.modificar_usuario_admin(
                usuario_id=usuario_id,
                datos_actualizados=datos_actualizados,
                admin_usuario=admin_usuario
            )
            
            return Response(
                {
                    'success': True,
                    'message': 'Usuario modificado exitosamente',
                    'data': {
                        'usuario_id': resultado['usuario'].id,
                        'username': resultado['usuario'].username,
                        'email': resultado['usuario'].email,
                        'rol': resultado['rol'],
                        'activo': resultado['usuario'].is_active,
                        'cambios_realizados': list(datos_actualizados.keys())
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            logger.warning(f"Error de validación al modificar usuario (admin): {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionError as e:
            logger.warning(f"Intento de modificar admin por otro admin: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Error inesperado al modificar usuario (admin): {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al procesar la solicitud'
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
# CU-06: ELIMINAR USUARIO (ADMINISTRADOR)
# ============================================================================

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def eliminar_usuario_admin_api(request, usuario_id):
    """
    Elimina un usuario por parte del administrador.
    
    El administrador puede:
    - Eliminar clientes y profesionales
    - Verificar condiciones antes de eliminar
    - Forzar eliminación aunque haya turnos/pagos activos (con precaución)
    - NO puede eliminar otros administradores
    
    Se realiza eliminación lógica (el usuario queda inactivo y sus datos se anonimizan).
    
    **Permisos**: Solo administradores
    
    **Método**: DELETE
    
    **URL**: /api/admin/usuarios/<id>/eliminar/
    
    **Parámetros URL**:
    - usuario_id: ID del usuario a eliminar
    
    **Body**:
    ```json
    {
        "confirmar": true,
        "forzar": false
    }
    ```
    
    **Respuestas**:
    - 200: Usuario eliminado exitosamente
    - 400: Error de validación o condiciones no cumplidas
    - 403: No tiene permisos o intenta eliminar otro admin
    - 404: Usuario no encontrado
    """
    serializer = AdminEliminarUsuarioSerializer(data=request.data)
    
    if serializer.is_valid():
        confirmar = serializer.validated_data['confirmar']
        forzar = serializer.validated_data.get('forzar', False)
        
        try:
            admin_usuario = request.user
            
            resultado = AdminUsuarioService.eliminar_usuario_admin(
                usuario_id=usuario_id,
                admin_usuario=admin_usuario,
                forzar=forzar
            )
            
            return Response(
                {
                    'success': True,
                    'message': 'Usuario eliminado exitosamente',
                    'data': {
                        'usuario_id': usuario_id,
                        'username_anonimizado': resultado.get('username_anonimizado', ''),
                        'forzado': forzar
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            logger.warning(f"Error al eliminar usuario (admin): {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionError as e:
            logger.warning(f"Intento de eliminar admin: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Error inesperado al eliminar usuario (admin): {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al procesar la solicitud'
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
# LISTAR USUARIOS CON FILTROS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def listar_usuarios_api(request):
    """
    Lista todos los usuarios con opciones de filtrado, búsqueda y paginación.
    
    **Permisos**: Solo administradores
    
    **Método**: GET
    
    **URL**: /api/admin/usuarios/
    
    **Query Parameters**:
    - rol: Filtrar por rol (cliente, profesional, administrador)
    - activo: Filtrar por estado (true/false)
    - busqueda: Buscar en nombre, email, username
    - orden: Campo de ordenamiento (username, email, fecha_registro, etc.)
          Usar "-" para orden descendente (ej: -fecha_registro)
    - pagina: Número de página (default: 1)
    - por_pagina: Elementos por página (default: 20, max: 100)
    
    **Ejemplo**: /api/admin/usuarios/?rol=profesional&activo=true&pagina=1&por_pagina=20
    
    **Respuestas**:
    - 200: Lista de usuarios
    - 400: Parámetros inválidos
    - 403: No tiene permisos de administrador
    """
    # Validar parámetros
    serializer = FiltrosUsuarioSerializer(data=request.query_params)
    
    if serializer.is_valid():
        filtros = serializer.validated_data
        
        try:
            resultado = AdminUsuarioService.listar_usuarios(filtros=filtros)
            
            # Preparar respuesta con datos del usuario
            usuarios_data = []
            for usuario in resultado['usuarios']:
                # Determinar el rol
                if usuario.is_staff and usuario.is_superuser:
                    rol = 'administrador'
                elif hasattr(usuario, 'profesional'):
                    rol = 'profesional'
                elif hasattr(usuario, 'cliente'):
                    rol = 'cliente'
                else:
                    rol = 'desconocido'
                
                usuario_info = {
                    'id': usuario.id,
                    'username': usuario.username,
                    'email': usuario.email,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'rol': rol,
                    'activo': usuario.is_active,
                    'fecha_registro': usuario.date_joined.isoformat() if usuario.date_joined else None,
                    'ultimo_acceso': usuario.last_login.isoformat() if usuario.last_login else None
                }
                
                # Agregar información específica del rol
                if rol == 'profesional' and hasattr(usuario, 'profesional'):
                    usuario_info['profesional'] = {
                        'anios_experiencia': usuario.profesional.anios_experiencia,
                        'calificacion_promedio': float(usuario.profesional.calificacion_promedio) if usuario.profesional.calificacion_promedio else None,
                        'servicios': [s.nombre for s in usuario.profesional.servicios.all()]
                    }
                
                usuarios_data.append(usuario_info)
            
            return Response(
                {
                    'success': True,
                    'data': {
                        'usuarios': usuarios_data,
                        'paginacion': {
                            'total': resultado['total'],
                            'pagina_actual': resultado['pagina_actual'],
                            'total_paginas': resultado['total_paginas'],
                            'por_pagina': resultado['por_pagina'],
                            'tiene_siguiente': resultado['tiene_siguiente'],
                            'tiene_anterior': resultado['tiene_anterior']
                        },
                        'filtros_aplicados': {
                            'rol': filtros.get('rol'),
                            'activo': filtros.get('activo'),
                            'busqueda': filtros.get('busqueda'),
                            'orden': filtros.get('orden', '-fecha_registro')
                        }
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error al listar usuarios: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Error interno al procesar la solicitud'
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
# OBTENER DETALLE DE UN USUARIO
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def obtener_usuario_api(request, usuario_id):
    """
    Obtiene el detalle completo de un usuario específico.
    
    **Permisos**: Solo administradores
    
    **Método**: GET
    
    **URL**: /api/admin/usuarios/<id>/
    
    **Parámetros URL**:
    - usuario_id: ID del usuario
    
    **Respuestas**:
    - 200: Datos del usuario
    - 403: No tiene permisos
    - 404: Usuario no encontrado
    """
    from .models import Usuario
    
    try:
        usuario = Usuario.objects.select_related('cliente', 'profesional').get(id=usuario_id)
        
        # Determinar el rol
        if usuario.is_staff and usuario.is_superuser:
            rol = 'administrador'
        elif hasattr(usuario, 'profesional'):
            rol = 'profesional'
        elif hasattr(usuario, 'cliente'):
            rol = 'cliente'
        else:
            rol = 'desconocido'
        
        usuario_data = {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'telefono': usuario.telefono,
            'direccion': usuario.direccion,
            'rol': rol,
            'activo': usuario.is_active,
            'email_confirmado': usuario.email_confirmado,
            'fecha_registro': usuario.date_joined.isoformat() if usuario.date_joined else None,
            'ultimo_acceso': usuario.last_login.isoformat() if usuario.last_login else None,
            'google_id': usuario.google_id if hasattr(usuario, 'google_id') else None
        }
        
        # Información específica del rol
        if rol == 'cliente' and hasattr(usuario, 'cliente'):
            usuario_data['cliente'] = {
                'id': usuario.cliente.id,
                'preferencias': usuario.cliente.preferencias
            }
        
        elif rol == 'profesional' and hasattr(usuario, 'profesional'):
            profesional = usuario.profesional
            usuario_data['profesional'] = {
                'id': profesional.id,
                'anios_experiencia': profesional.anios_experiencia,
                'calificacion_promedio': float(profesional.calificacion_promedio) if profesional.calificacion_promedio else None,
                'servicios': [
                    {
                        'id': s.id,
                        'nombre': s.nombre,
                        'categoria': s.categoria.nombre if hasattr(s, 'categoria') else None
                    }
                    for s in profesional.servicios.all()
                ],
                'horarios': list(profesional.horarios.values(
                    'dia_semana', 'hora_inicio', 'hora_fin', 'activo'
                ))
            }
        
        return Response(
            {
                'success': True,
                'data': usuario_data
            },
            status=status.HTTP_200_OK
        )
        
    except Usuario.DoesNotExist:
        return Response(
            {
                'success': False,
                'error': 'Usuario no encontrado'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al obtener usuario: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'Error interno al procesar la solicitud'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
