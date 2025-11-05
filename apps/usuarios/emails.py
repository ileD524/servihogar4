"""
Utilidades para envío de emails en la aplicación de usuarios.
Maneja confirmación de registro, notificaciones de baja, etc.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio para gestión de emails relacionados con usuarios.
    """
    
    @staticmethod
    def enviar_email_confirmacion(usuario, request):
        """
        Envía email de confirmación de registro con enlace de activación.
        
        Args:
            usuario (Usuario): Usuario recién registrado
            request: Request de Django para construir URL absoluta
            
        Returns:
            bool: True si el email se envió exitosamente
        """
        try:
            # Generar token de confirmación
            token = default_token_generator.make_token(usuario)
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            
            # Construir URL de confirmación
            # Formato: /usuarios/confirmar/<uidb64>/<token>/
            url_confirmacion = request.build_absolute_uri(
                reverse('usuarios:confirmar_email', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Preparar email
            asunto = 'ServiHogar - Confirma tu registro'
            mensaje = f"""
            Hola {usuario.first_name},
            
            Gracias por registrarte en ServiHogar.
            
            Para completar tu registro, por favor confirma tu email haciendo clic en el siguiente enlace:
            
            {url_confirmacion}
            
            Este enlace expirará en 24 horas.
            
            Si no te registraste en ServiHogar, puedes ignorar este email.
            
            Saludos,
            El equipo de ServiHogar
            """
            
            email_desde = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@servihogar.com'
            
            send_mail(
                asunto,
                mensaje,
                email_desde,
                [usuario.email],
                fail_silently=False,
            )
            
            logger.info(f"Email de confirmación enviado a {usuario.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de confirmación: {str(e)}")
            return False
    
    @staticmethod
    def enviar_email_baja(usuario):
        """
        Envía email de notificación de baja de cuenta.
        
        Args:
            usuario (Usuario): Usuario que se dio de baja
            
        Returns:
            bool: True si el email se envió exitosamente
        """
        try:
            asunto = 'ServiHogar - Confirmación de baja'
            mensaje = f"""
            Hola {usuario.first_name},
            
            Tu cuenta en ServiHogar ha sido dada de baja exitosamente.
            
            Lamentamos verte partir. Si cambias de opinión, siempre serás bienvenido a crear una nueva cuenta.
            
            Todos tus datos personales han sido eliminados de nuestro sistema.
            
            Gracias por haber sido parte de ServiHogar.
            
            Saludos,
            El equipo de ServiHogar
            """
            
            email_desde = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@servihogar.com'
            
            send_mail(
                asunto,
                mensaje,
                email_desde,
                [usuario.email],
                fail_silently=False,
            )
            
            logger.info(f"Email de baja enviado a {usuario.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de baja: {str(e)}")
            return False
    
    @staticmethod
    def enviar_email_bienvenida(usuario):
        """
        Envía email de bienvenida tras confirmar el registro.
        
        Args:
            usuario (Usuario): Usuario recién confirmado
            
        Returns:
            bool: True si el email se envió exitosamente
        """
        try:
            asunto = '¡Bienvenido a ServiHogar!'
            
            # Mensaje personalizado según el rol
            if usuario.is_cliente():
                mensaje_especifico = "Ya puedes empezar a buscar servicios y solicitar turnos con nuestros profesionales."
            elif usuario.is_profesional():
                mensaje_especifico = "Ya puedes gestionar tus servicios y comenzar a recibir solicitudes de clientes."
            else:
                mensaje_especifico = "Tu cuenta ha sido activada exitosamente."
            
            mensaje = f"""
            Hola {usuario.first_name},
            
            ¡Tu cuenta en ServiHogar ha sido confirmada exitosamente!
            
            {mensaje_especifico}
            
            Visita nuestra plataforma en cualquier momento: http://servihogar.com
            
            Si tienes alguna pregunta, no dudes en contactarnos.
            
            ¡Que disfrutes la experiencia ServiHogar!
            
            Saludos,
            El equipo de ServiHogar
            """
            
            email_desde = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@servihogar.com'
            
            send_mail(
                asunto,
                mensaje,
                email_desde,
                [usuario.email],
                fail_silently=False,
            )
            
            logger.info(f"Email de bienvenida enviado a {usuario.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de bienvenida: {str(e)}")
            return False
    
    @staticmethod
    def enviar_email_actualizacion_perfil(usuario):
        """
        Envía email de notificación de actualización de perfil.
        
        Args:
            usuario (Usuario): Usuario que actualizó su perfil
            
        Returns:
            bool: True si el email se envió exitosamente
        """
        try:
            asunto = 'ServiHogar - Perfil actualizado'
            mensaje = f"""
            Hola {usuario.first_name},
            
            Tu perfil en ServiHogar ha sido actualizado exitosamente.
            
            Si no realizaste estos cambios, por favor contacta a nuestro equipo de soporte inmediatamente.
            
            Saludos,
            El equipo de ServiHogar
            """
            
            email_desde = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@servihogar.com'
            
            send_mail(
                asunto,
                mensaje,
                email_desde,
                [usuario.email],
                fail_silently=False,
            )
            
            logger.info(f"Email de actualización enviado a {usuario.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de actualización: {str(e)}")
            return False
