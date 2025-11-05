"""
Servicios de negocio para la gestión de usuarios.
Contiene toda la lógica de negocio separada de las vistas.
Implementa los casos de uso CU-01, CU-02 y CU-03.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import datetime
import logging

from .models import Usuario, Cliente, Profesional, HorarioDisponibilidad
from .validators import UsuarioValidator, PerfilValidator
from .emails import EmailService

logger = logging.getLogger(__name__)


class UsuarioService:
    """
    Servicio para gestión de usuarios.
    Implementa lógica de negocio de los casos de uso.
    """
    
    @staticmethod
    @transaction.atomic
    def registrar_usuario_manual(datos_usuario, datos_perfil=None, request=None):
        """
        CU-01: Registrar usuario con datos manuales (no Google).
        
        Args:
            datos_usuario (dict): Diccionario con datos básicos del usuario:
                - username (str): Nombre de usuario
                - email (str): Email
                - password (str): Contraseña
                - first_name (str): Nombre
                - last_name (str): Apellido
                - telefono (str, optional): Teléfono
                - direccion (str, optional): Dirección
                - rol (str): 'cliente' o 'profesional'
            datos_perfil (dict, optional): Datos adicionales según el rol:
                - Para profesionales: servicios, horarios, anios_experiencia
            request: Request de Django para enviar email de confirmación
            
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
            
            # 2. Validar contraseña
            password = datos_usuario.get('password', '')
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
                    UsuarioValidator.validar_datos_completos_profesional(datos_perfil)
                    if 'horarios' in datos_perfil:
                        UsuarioValidator.validar_horarios(datos_perfil['horarios'])
                except ValidationError as e:
                    errores.extend(e.messages)
            
            # Si hay errores, no continuar
            if errores:
                raise ValidationError(errores)
            
            # 6. Crear usuario
            usuario = Usuario.objects.create(
                username=datos_usuario.get('username'),
                email=email,
                first_name=datos_usuario.get('first_name', ''),
                last_name=datos_usuario.get('last_name', ''),
                telefono=telefono,
                direccion=datos_usuario.get('direccion', ''),
                rol=rol,
                activo=False,  # Inactivo hasta confirmar email
                is_active=False,  # Django field para login
            )
            
            # Establecer contraseña encriptada
            usuario.set_password(password)
            usuario.save()
            
            # 7. Crear perfil según rol
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
            
            # 8. Enviar email de confirmación
            if request:
                email_enviado = EmailService.enviar_email_confirmacion(usuario, request)
                if not email_enviado:
                    logger.warning(f"No se pudo enviar email de confirmación a {usuario.email}")
            
            logger.info(f"Usuario {usuario.username} registrado exitosamente (pendiente de confirmación)")
            return usuario, []
            
        except ValidationError as e:
            # Si es una ValidationError de Django, extraer mensajes
            if hasattr(e, 'messages'):
                raise ValidationError(e.messages)
            raise
        except Exception as e:
            logger.error(f"Error al registrar usuario: {str(e)}")
            raise ValidationError(f"Error al registrar usuario: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def registrar_usuario_google(google_data):
        """
        CU-01: Registrar usuario autenticado por Google.
        Solo se obtiene nombre y email de Google, el resto debe completarlo el usuario.
        
        Args:
            google_data (dict): Datos obtenidos de Google:
                - google_id (str): ID de Google
                - email (str): Email
                - first_name (str): Nombre
                - last_name (str): Apellido
                
        Returns:
            Usuario: Usuario creado o existente
            
        Raises:
            ValidationError: Si hay errores de validación
        """
        try:
            google_id = google_data.get('google_id')
            email = google_data.get('email', '').strip().lower()
            
            # Validar email
            UsuarioValidator.validar_email_formato(email)
            
            # Buscar si ya existe usuario con este google_id
            usuario = Usuario.objects.filter(google_id=google_id).first()
            
            if usuario:
                # Usuario ya existe, retornarlo
                logger.info(f"Usuario existente con Google ID {google_id}")
                return usuario
            
            # Buscar si existe usuario con este email
            usuario_existente = Usuario.objects.filter(email=email).first()
            if usuario_existente:
                # Vincular cuenta existente con Google
                usuario_existente.google_id = google_id
                usuario_existente.save()
                logger.info(f"Cuenta existente vinculada con Google: {email}")
                return usuario_existente
            
            # Crear nuevo usuario
            username = email.split('@')[0]
            
            # Asegurar que el username sea único
            username_base = username
            contador = 1
            while Usuario.objects.filter(username=username).exists():
                username = f"{username_base}{contador}"
                contador += 1
            
            usuario = Usuario.objects.create(
                username=username,
                email=email,
                first_name=google_data.get('first_name', ''),
                last_name=google_data.get('last_name', ''),
                google_id=google_id,
                rol='cliente',  # Por defecto es cliente
                activo=True,  # Ya está verificado por Google
                is_active=True,
            )
            
            # No establecer password (autenticación por Google)
            usuario.set_unusable_password()
            usuario.save()
            
            # Crear perfil de cliente por defecto
            Cliente.objects.create(usuario=usuario)
            
            logger.info(f"Usuario creado con Google: {usuario.username}")
            return usuario
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al registrar usuario con Google: {str(e)}")
            raise ValidationError(f"Error al registrar usuario con Google: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def completar_datos_usuario_google(usuario_id, datos_adicionales):
        """
        CU-01: Completar datos de usuario registrado por Google.
        Permite al usuario agregar/actualizar información adicional.
        
        Args:
            usuario_id (int): ID del usuario
            datos_adicionales (dict): Datos a completar:
                - telefono (str, optional)
                - direccion (str, optional)
                - rol (str, optional): Cambiar de cliente a profesional
                - datos_perfil (dict, optional): Datos específicos del rol
                
        Returns:
            Usuario: Usuario actualizado
            
        Raises:
            ValidationError: Si hay errores de validación
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # Validar que sea usuario de Google
            if not usuario.google_id:
                raise ValidationError("Este método es solo para usuarios registrados con Google")
            
            # Validar teléfono si se proporciona
            if 'telefono' in datos_adicionales:
                UsuarioValidator.validar_telefono(datos_adicionales['telefono'])
                usuario.telefono = datos_adicionales['telefono']
            
            # Actualizar dirección
            if 'direccion' in datos_adicionales:
                usuario.direccion = datos_adicionales['direccion']
            
            # Actualizar rol si se proporciona
            if 'rol' in datos_adicionales:
                nuevo_rol = datos_adicionales['rol']
                
                if nuevo_rol not in ['cliente', 'profesional']:
                    raise ValidationError("El rol debe ser 'cliente' o 'profesional'")
                
                # Si cambia a profesional, crear perfil profesional
                if nuevo_rol == 'profesional' and usuario.rol == 'cliente':
                    # Eliminar perfil de cliente
                    if hasattr(usuario, 'perfil_cliente'):
                        usuario.perfil_cliente.delete()
                    
                    # Validar datos de profesional
                    datos_perfil = datos_adicionales.get('datos_perfil', {})
                    UsuarioValidator.validar_datos_completos_profesional(datos_perfil)
                    
                    if 'horarios' in datos_perfil:
                        UsuarioValidator.validar_horarios(datos_perfil['horarios'])
                    
                    # Crear perfil profesional
                    profesional = Profesional.objects.create(
                        usuario=usuario,
                        anios_experiencia=datos_perfil.get('anios_experiencia', 0)
                    )
                    
                    # Crear horarios
                    if 'horarios' in datos_perfil:
                        for horario_data in datos_perfil['horarios']:
                            HorarioDisponibilidad.objects.create(
                                profesional=profesional,
                                dia_semana=horario_data['dia'],
                                hora_inicio=horario_data['hora_inicio'],
                                hora_fin=horario_data['hora_fin']
                            )
                    
                    usuario.rol = nuevo_rol
            
            usuario.save()
            logger.info(f"Datos completados para usuario {usuario.username}")
            return usuario
            
        except Usuario.DoesNotExist:
            raise ValidationError("Usuario no encontrado")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al completar datos de usuario: {str(e)}")
            raise ValidationError(f"Error al completar datos: {str(e)}")
    
    @staticmethod
    def confirmar_email(usuario_id):
        """
        CU-01: Confirmar email de usuario y activar cuenta.
        Cambia el estado de 'Pendiente' a 'Activo'.
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            Usuario: Usuario activado
            
        Raises:
            ValidationError: Si hay errores
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            if usuario.activo and usuario.is_active:
                logger.info(f"Usuario {usuario.username} ya estaba activado")
                return usuario
            
            # Activar usuario
            usuario.activo = True
            usuario.is_active = True
            usuario.save()
            
            # Enviar email de bienvenida
            EmailService.enviar_email_bienvenida(usuario)
            
            logger.info(f"Email confirmado para usuario {usuario.username}")
            return usuario
            
        except Usuario.DoesNotExist:
            raise ValidationError("Usuario no encontrado")
        except Exception as e:
            logger.error(f"Error al confirmar email: {str(e)}")
            raise ValidationError(f"Error al confirmar email: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def modificar_perfil(usuario_id, datos_actualizados, datos_perfil=None):
        """
        CU-03: Modificar perfil de usuario autenticado.
        
        Args:
            usuario_id (int): ID del usuario a modificar
            datos_actualizados (dict): Datos a actualizar:
                - first_name (str, optional)
                - last_name (str, optional)
                - email (str, optional)
                - telefono (str, optional)
                - direccion (str, optional)
            datos_perfil (dict, optional): Datos específicos del perfil según rol
            
        Returns:
            Usuario: Usuario actualizado
            
        Raises:
            ValidationError: Si hay errores de validación
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
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
            
            usuario.fecha_modificacion = timezone.now()
            usuario.save()
            
            # Actualizar datos específicos según rol
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
            
            # Enviar email de notificación
            EmailService.enviar_email_actualizacion_perfil(usuario)
            
            logger.info(f"Perfil actualizado para usuario {usuario.username}")
            return usuario
            
        except Usuario.DoesNotExist:
            raise ValidationError("Usuario no encontrado")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al modificar perfil: {str(e)}")
            raise ValidationError(f"Error al modificar perfil: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def eliminar_perfil(usuario_id):
        """
        CU-02: Eliminar perfil de usuario (baja lógica).
        Solo se puede ejecutar si no hay turnos activos ni pagos pendientes.
        
        Args:
            usuario_id (int): ID del usuario a eliminar
            
        Returns:
            dict: Información sobre la eliminación
            
        Raises:
            ValidationError: Si no cumple condiciones para eliminar
        """
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # Validar que puede eliminar el perfil
            puede_eliminar, mensaje_error = PerfilValidator.puede_eliminar_perfil(usuario)
            
            if not puede_eliminar:
                raise ValidationError(mensaje_error)
            
            # Guardar email para enviar notificación (antes de anonimizar)
            email_original = usuario.email
            
            # Realizar baja lógica
            # Anonimizar datos personales pero mantener registro para auditoría
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
            
            # Enviar email de confirmación de baja
            # Crear un objeto temporal con el email original para enviar el correo
            class UsuarioTemp:
                def __init__(self, email, first_name):
                    self.email = email
                    self.first_name = first_name
            
            usuario_temp = UsuarioTemp(email_original, usuario.first_name)
            EmailService.enviar_email_baja(usuario_temp)
            
            logger.info(f"Perfil eliminado para usuario ID {usuario_id}")
            
            return {
                'success': True,
                'usuario_id': usuario_id,
                'fecha_eliminacion': usuario.fecha_eliminacion,
                'mensaje': 'Perfil eliminado exitosamente'
            }
            
        except Usuario.DoesNotExist:
            raise ValidationError("Usuario no encontrado")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al eliminar perfil: {str(e)}")
            raise ValidationError(f"Error al eliminar perfil: {str(e)}")
