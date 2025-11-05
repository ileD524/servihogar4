"""
Servicios administrativos para la gestión de usuarios.
Estos servicios solo pueden ser ejecutados por administradores.
Implementa los casos de uso CU-04, CU-05 y CU-06.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import logging

from .models import Usuario, Cliente, Profesional, HorarioDisponibilidad
from .validators import UsuarioValidator, PerfilValidator
from .emails import EmailService

logger = logging.getLogger(__name__)


class AdminUsuarioService:
    """
    Servicio para gestión administrativa de usuarios.
    Solo accesible por administradores autenticados.
    """
    
    @staticmethod
    @transaction.atomic
    def registrar_usuario_admin(datos_usuario, datos_perfil=None, admin_id=None, request=None):
        """
        CU-04: Registrar usuario por parte del administrador.
        El administrador puede crear clientes o profesionales.
        
        Args:
            datos_usuario (dict): Datos básicos del usuario:
                - username (str): Nombre de usuario
                - email (str): Email
                - password (str, optional): Contraseña (no requerida si es Google)
                - first_name (str): Nombre
                - last_name (str): Apellido
                - telefono (str, optional): Teléfono
                - direccion (str, optional): Dirección
                - rol (str): 'cliente' o 'profesional'
                - google_id (str, optional): ID de Google si es registro OAuth
                - estado (str, optional): 'activo' o 'pendiente' (default: 'activo')
            datos_perfil (dict, optional): Datos específicos del rol:
                - Para profesionales: servicios, horarios, anios_experiencia
            admin_id (int): ID del administrador que crea el usuario
            request: Request de Django para enviar email
            
        Returns:
            tuple: (Usuario, list[str]) - (usuario_creado, lista_errores)
            
        Raises:
            ValidationError: Si hay errores de validación
        """
        errores = []
        
        try:
            # 1. Validar email
            email = datos_usuario.get('email', '').strip().lower()
            try:
                UsuarioValidator.validar_email_formato(email)
                UsuarioValidator.validar_email_unico(email)
            except ValidationError as e:
                errores.extend(e.messages)
            
            # 2. Validar contraseña (solo si no es Google OAuth)
            google_id = datos_usuario.get('google_id')
            password = datos_usuario.get('password', '')
            
            if not google_id:
                # Usuario manual requiere contraseña
                if not password:
                    errores.append("La contraseña es requerida para usuarios manuales")
                else:
                    try:
                        UsuarioValidator.validar_contrasena_segura(password)
                    except ValidationError as e:
                        errores.extend(e.messages)
            
            # 3. Validar teléfono
            telefono = datos_usuario.get('telefono', '')
            try:
                UsuarioValidator.validar_telefono(telefono)
            except ValidationError as e:
                errores.extend(e.messages)
            
            # 4. Validar rol
            rol = datos_usuario.get('rol', 'cliente')
            if rol not in ['cliente', 'profesional']:
                errores.append("El rol debe ser 'cliente' o 'profesional'")
            
            # 5. Si es profesional, validar datos adicionales
            if rol == 'profesional' and datos_perfil:
                try:
                    if 'servicios' not in datos_perfil or not datos_perfil['servicios']:
                        errores.append("Los profesionales deben tener al menos un servicio asignado")
                    
                    if 'horarios' in datos_perfil and datos_perfil['horarios']:
                        UsuarioValidator.validar_horarios(datos_perfil['horarios'])
                except ValidationError as e:
                    errores.extend(e.messages)
            
            # Si hay errores, no continuar
            if errores:
                raise ValidationError(errores)
            
            # 6. Determinar estado inicial
            # El admin puede crear usuarios directamente activos o pendientes
            estado = datos_usuario.get('estado', 'activo')
            if estado not in ['activo', 'pendiente']:
                estado = 'activo'  # Por defecto activo cuando lo crea el admin
            
            activo = (estado == 'activo')
            
            # 7. Crear usuario
            usuario = Usuario.objects.create(
                username=datos_usuario.get('username'),
                email=email,
                first_name=datos_usuario.get('first_name', ''),
                last_name=datos_usuario.get('last_name', ''),
                telefono=telefono,
                direccion=datos_usuario.get('direccion', ''),
                rol=rol,
                activo=activo,
                is_active=activo,
                google_id=google_id,
            )
            
            # Establecer contraseña
            if password:
                usuario.set_password(password)
            elif google_id:
                usuario.set_unusable_password()
            else:
                # Generar contraseña temporal si el admin no proporcionó una
                import secrets
                temp_password = secrets.token_urlsafe(12)
                usuario.set_password(temp_password)
                logger.info(f"Contraseña temporal generada para usuario {usuario.username}")
            
            usuario.save()
            
            # 8. Crear perfil según rol
            if rol == 'cliente':
                Cliente.objects.create(usuario=usuario)
            
            elif rol == 'profesional':
                profesional = Profesional.objects.create(
                    usuario=usuario,
                    anios_experiencia=datos_perfil.get('anios_experiencia', 0) if datos_perfil else 0
                )
                
                # Asignar servicios si se proporcionaron
                if datos_perfil and 'servicios' in datos_perfil:
                    from apps.servicios.models import Servicio
                    for servicio_id in datos_perfil['servicios']:
                        try:
                            servicio = Servicio.objects.get(id=servicio_id, activo=True)
                            servicio.profesional = profesional
                            servicio.save()
                        except Servicio.DoesNotExist:
                            logger.warning(f"Servicio {servicio_id} no encontrado")
                
                # Crear horarios de disponibilidad
                if datos_perfil and 'horarios' in datos_perfil:
                    for horario_data in datos_perfil['horarios']:
                        HorarioDisponibilidad.objects.create(
                            profesional=profesional,
                            dia_semana=horario_data['dia'],
                            hora_inicio=horario_data['hora_inicio'],
                            hora_fin=horario_data['hora_fin']
                        )
            
            # 9. Enviar email de confirmación o bienvenida
            if request:
                if activo:
                    # Si está activo, enviar bienvenida directa
                    EmailService.enviar_email_bienvenida(usuario)
                else:
                    # Si está pendiente, enviar confirmación
                    EmailService.enviar_email_confirmacion(usuario, request)
            
            logger.info(
                f"Usuario {usuario.username} creado por administrador ID {admin_id}. "
                f"Estado: {estado}"
            )
            
            return usuario, []
            
        except ValidationError as e:
            if hasattr(e, 'messages'):
                raise ValidationError(e.messages)
            raise
        except Exception as e:
            logger.error(f"Error al registrar usuario (admin): {str(e)}")
            raise ValidationError(f"Error al registrar usuario: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def modificar_usuario_admin(usuario_id, datos_actualizados, datos_perfil=None, admin_id=None):
        """
        CU-05: Modificar usuario por parte del administrador.
        El administrador puede modificar cualquier campo de cualquier usuario.
        
        Args:
            usuario_id (int): ID del usuario a modificar
            datos_actualizados (dict): Datos a actualizar:
                - username (str, optional)
                - first_name (str, optional)
                - last_name (str, optional)
                - email (str, optional)
                - telefono (str, optional)
                - direccion (str, optional)
                - rol (str, optional): Puede cambiar entre cliente/profesional
                - activo (bool, optional): El admin puede activar/desactivar
            datos_perfil (dict, optional): Datos específicos del perfil según rol
            admin_id (int): ID del administrador que modifica
            
        Returns:
            Usuario: Usuario actualizado
            
        Raises:
            ValidationError: Si hay errores de validación
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # El admin NO puede modificar a otros admins (regla de seguridad)
            if usuario.is_administrador():
                raise ValidationError(
                    "Los administradores no pueden modificar a otros administradores. "
                    "Use el panel de administración de Django para esto."
                )
            
            # Validar username si se cambió
            if 'username' in datos_actualizados:
                nuevo_username = datos_actualizados['username']
                if nuevo_username != usuario.username:
                    if Usuario.objects.filter(username=nuevo_username).exists():
                        raise ValidationError("Este nombre de usuario ya está en uso")
                    usuario.username = nuevo_username
            
            # Validar email si se cambió
            if 'email' in datos_actualizados:
                nuevo_email = datos_actualizados['email'].strip().lower()
                if nuevo_email != usuario.email:
                    UsuarioValidator.validar_email_formato(nuevo_email)
                    UsuarioValidator.validar_email_unico(nuevo_email, excluir_usuario_id=usuario_id)
                    usuario.email = nuevo_email
            
            # Validar y actualizar teléfono
            if 'telefono' in datos_actualizados:
                UsuarioValidator.validar_telefono(datos_actualizados['telefono'])
                usuario.telefono = datos_actualizados['telefono']
            
            # Actualizar campos básicos
            if 'first_name' in datos_actualizados:
                usuario.first_name = datos_actualizados['first_name']
            
            if 'last_name' in datos_actualizados:
                usuario.last_name = datos_actualizados['last_name']
            
            if 'direccion' in datos_actualizados:
                usuario.direccion = datos_actualizados['direccion']
            
            # El admin puede cambiar el estado activo/inactivo
            if 'activo' in datos_actualizados:
                nuevo_activo = bool(datos_actualizados['activo'])
                usuario.activo = nuevo_activo
                usuario.is_active = nuevo_activo
            
            # El admin puede cambiar el rol (pero con precauciones)
            if 'rol' in datos_actualizados:
                nuevo_rol = datos_actualizados['rol']
                
                if nuevo_rol not in ['cliente', 'profesional']:
                    raise ValidationError("El rol debe ser 'cliente' o 'profesional'")
                
                if nuevo_rol != usuario.rol:
                    # Cambio de rol
                    rol_anterior = usuario.rol
                    
                    # Validar que no tenga turnos activos
                    from apps.turnos.models import Turno
                    
                    if rol_anterior == 'cliente':
                        turnos_activos = Turno.objects.filter(
                            cliente=usuario.perfil_cliente,
                            estado__in=['pendiente', 'confirmado', 'en_curso']
                        ).exists()
                        
                        if turnos_activos:
                            raise ValidationError(
                                "No se puede cambiar el rol porque el usuario tiene turnos activos como cliente"
                            )
                        
                        # Eliminar perfil de cliente
                        usuario.perfil_cliente.delete()
                    
                    elif rol_anterior == 'profesional':
                        turnos_activos = Turno.objects.filter(
                            profesional=usuario.perfil_profesional,
                            estado__in=['pendiente', 'confirmado', 'en_curso']
                        ).exists()
                        
                        if turnos_activos:
                            raise ValidationError(
                                "No se puede cambiar el rol porque el usuario tiene turnos activos como profesional"
                            )
                        
                        # Eliminar perfil de profesional y desasociar servicios
                        from apps.servicios.models import Servicio
                        Servicio.objects.filter(profesional=usuario.perfil_profesional).update(profesional=None)
                        HorarioDisponibilidad.objects.filter(profesional=usuario.perfil_profesional).delete()
                        usuario.perfil_profesional.delete()
                    
                    # Crear nuevo perfil según el nuevo rol
                    if nuevo_rol == 'cliente':
                        Cliente.objects.create(usuario=usuario)
                    elif nuevo_rol == 'profesional':
                        if not datos_perfil or 'servicios' not in datos_perfil or not datos_perfil['servicios']:
                            raise ValidationError(
                                "Para cambiar a profesional debe proporcionar al menos un servicio"
                            )
                        
                        profesional = Profesional.objects.create(
                            usuario=usuario,
                            anios_experiencia=datos_perfil.get('anios_experiencia', 0) if datos_perfil else 0
                        )
                        
                        # Asignar servicios
                        from apps.servicios.models import Servicio
                        for servicio_id in datos_perfil['servicios']:
                            try:
                                servicio = Servicio.objects.get(id=servicio_id, activo=True)
                                servicio.profesional = profesional
                                servicio.save()
                            except Servicio.DoesNotExist:
                                logger.warning(f"Servicio {servicio_id} no encontrado")
                        
                        # Crear horarios si se proporcionaron
                        if datos_perfil and 'horarios' in datos_perfil:
                            UsuarioValidator.validar_horarios(datos_perfil['horarios'])
                            for horario_data in datos_perfil['horarios']:
                                HorarioDisponibilidad.objects.create(
                                    profesional=profesional,
                                    dia_semana=horario_data['dia'],
                                    hora_inicio=horario_data['hora_inicio'],
                                    hora_fin=horario_data['hora_fin']
                                )
                    
                    usuario.rol = nuevo_rol
            
            # Actualizar datos específicos según rol (sin cambiar el rol)
            if usuario.is_profesional() and datos_perfil:
                profesional = usuario.perfil_profesional
                
                # Actualizar años de experiencia
                if 'anios_experiencia' in datos_perfil:
                    profesional.anios_experiencia = datos_perfil['anios_experiencia']
                    profesional.save()
                
                # Actualizar servicios
                if 'servicios' in datos_perfil:
                    from apps.servicios.models import Servicio
                    # Desasignar servicios actuales
                    Servicio.objects.filter(profesional=profesional).update(profesional=None)
                    
                    # Asignar nuevos servicios
                    for servicio_id in datos_perfil['servicios']:
                        try:
                            servicio = Servicio.objects.get(id=servicio_id, activo=True)
                            servicio.profesional = profesional
                            servicio.save()
                        except Servicio.DoesNotExist:
                            logger.warning(f"Servicio {servicio_id} no encontrado")
                
                # Actualizar horarios
                if 'horarios' in datos_perfil:
                    UsuarioValidator.validar_horarios(datos_perfil['horarios'])
                    
                    # Eliminar horarios existentes
                    HorarioDisponibilidad.objects.filter(profesional=profesional).delete()
                    
                    # Crear nuevos horarios
                    for horario_data in datos_perfil['horarios']:
                        HorarioDisponibilidad.objects.create(
                            profesional=profesional,
                            dia_semana=horario_data['dia'],
                            hora_inicio=horario_data['hora_inicio'],
                            hora_fin=horario_data['hora_fin']
                        )
            
            usuario.fecha_modificacion = timezone.now()
            usuario.save()
            
            logger.info(
                f"Usuario {usuario.username} (ID: {usuario_id}) modificado por "
                f"administrador ID {admin_id}"
            )
            
            return usuario
            
        except Usuario.DoesNotExist:
            raise ValidationError("Usuario no encontrado")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al modificar usuario (admin): {str(e)}")
            raise ValidationError(f"Error al modificar usuario: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def eliminar_usuario_admin(usuario_id, admin_id=None, forzar=False):
        """
        CU-06: Eliminar usuario por parte del administrador.
        
        Validaciones antes de eliminar:
        - No tener turnos activos/pendientes (a menos que se fuerce)
        - No tener pagos pendientes (a menos que se fuerce)
        
        Args:
            usuario_id (int): ID del usuario a eliminar
            admin_id (int): ID del administrador que elimina
            forzar (bool): Si es True, elimina aunque haya turnos/pagos
                          (usar con precaución)
            
        Returns:
            dict: Información sobre la eliminación
            
        Raises:
            ValidationError: Si no cumple condiciones para eliminar
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # Protección: NO se puede eliminar a administradores
            if usuario.is_administrador():
                raise ValidationError(
                    "No se puede eliminar a un administrador. "
                    "Use el panel de administración de Django para gestionar administradores."
                )
            
            # Validar que puede eliminar el perfil (a menos que se fuerce)
            if not forzar:
                puede_eliminar, mensaje_error = PerfilValidator.puede_eliminar_perfil(usuario)
                
                if not puede_eliminar:
                    raise ValidationError(mensaje_error)
            else:
                logger.warning(
                    f"Eliminación FORZADA de usuario {usuario.username} (ID: {usuario_id}) "
                    f"por administrador ID {admin_id}"
                )
            
            # Guardar email para enviar notificación (antes de anonimizar)
            email_original = usuario.email
            nombre_original = usuario.get_full_name()
            
            # Realizar baja lógica
            usuario.activo = False
            usuario.is_active = False
            usuario.fecha_eliminacion = timezone.now()
            
            # Anonimizar datos sensibles
            usuario.first_name = "Usuario"
            usuario.last_name = "Eliminado"
            usuario.email = f"eliminado_{usuario.id}@servihogar.local"
            usuario.telefono = ""
            usuario.direccion = ""
            usuario.username = f"eliminado_{usuario.id}"
            
            # Eliminar foto de perfil si existe
            if usuario.foto_perfil:
                usuario.foto_perfil.delete()
            
            usuario.save()
            
            # Eliminar datos de perfiles asociados
            if usuario.is_cliente() and hasattr(usuario, 'perfil_cliente'):
                cliente = usuario.perfil_cliente
                cliente.preferencias = ""
                cliente.historial_busquedas = ""
                cliente.save()
            
            elif usuario.is_profesional() and hasattr(usuario, 'perfil_profesional'):
                profesional = usuario.perfil_profesional
                profesional.especialidades = ""
                profesional.certificaciones = ""
                profesional.disponible = False
                profesional.save()
                
                # Eliminar horarios
                HorarioDisponibilidad.objects.filter(profesional=profesional).delete()
                
                # Desasociar servicios
                from apps.servicios.models import Servicio
                Servicio.objects.filter(profesional=profesional).update(profesional=None)
            
            # Enviar email de baja
            class UsuarioTemp:
                def __init__(self, email, first_name):
                    self.email = email
                    self.first_name = first_name
            
            usuario_temp = UsuarioTemp(email_original, nombre_original.split()[0] if nombre_original else "Usuario")
            EmailService.enviar_email_baja(usuario_temp)
            
            logger.info(
                f"Usuario {nombre_original} (ID: {usuario_id}) eliminado por "
                f"administrador ID {admin_id}"
            )
            
            return {
                'success': True,
                'usuario_id': usuario_id,
                'fecha_eliminacion': usuario.fecha_eliminacion,
                'mensaje': f'Usuario {nombre_original} eliminado exitosamente',
                'forzado': forzar
            }
            
        except Usuario.DoesNotExist:
            raise ValidationError("Usuario no encontrado")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al eliminar usuario (admin): {str(e)}")
            raise ValidationError(f"Error al eliminar usuario: {str(e)}")
    
    @staticmethod
    def listar_usuarios(filtros=None, orden=None, pagina=1, por_pagina=20):
        """
        Listar usuarios con filtros y paginación.
        
        Args:
            filtros (dict, optional): Filtros a aplicar:
                - rol: 'cliente', 'profesional', 'administrador'
                - activo: True/False
                - busqueda: texto para buscar en nombre, email, username
            orden (str, optional): Campo por el que ordenar (ej: '-fecha_registro')
            pagina (int): Número de página (inicia en 1)
            por_pagina (int): Cantidad de resultados por página
            
        Returns:
            dict: Diccionario con usuarios y metadata de paginación
        """
        try:
            queryset = Usuario.objects.all()
            
            # Aplicar filtros
            if filtros:
                if 'rol' in filtros:
                    queryset = queryset.filter(rol=filtros['rol'])
                
                if 'activo' in filtros:
                    queryset = queryset.filter(activo=filtros['activo'])
                
                if 'busqueda' in filtros and filtros['busqueda']:
                    from django.db.models import Q
                    busqueda = filtros['busqueda']
                    queryset = queryset.filter(
                        Q(username__icontains=busqueda) |
                        Q(email__icontains=busqueda) |
                        Q(first_name__icontains=busqueda) |
                        Q(last_name__icontains=busqueda)
                    )
            
            # Aplicar orden
            if orden:
                queryset = queryset.order_by(orden)
            else:
                queryset = queryset.order_by('-fecha_registro')
            
            # Calcular paginación
            total = queryset.count()
            inicio = (pagina - 1) * por_pagina
            fin = inicio + por_pagina
            
            usuarios = list(queryset[inicio:fin])
            
            return {
                'usuarios': usuarios,
                'total': total,
                'pagina': pagina,
                'por_pagina': por_pagina,
                'total_paginas': (total + por_pagina - 1) // por_pagina,
            }
            
        except Exception as e:
            logger.error(f"Error al listar usuarios: {str(e)}")
            raise ValidationError(f"Error al listar usuarios: {str(e)}")
