"""
Validators para la aplicación de usuarios.
Contiene todas las validaciones de negocio separadas de los modelos y vistas.
"""
import re
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password as django_validate_password
from .models import Usuario


class UsuarioValidator:
    """
    Clase con métodos estáticos para validar datos de usuarios.
    Implementa validaciones de negocio sin dependencia de modelos o vistas.
    """
    
    @staticmethod
    def validar_email_formato(email):
        """
        Valida que el email tenga un formato válido.
        
        Args:
            email (str): Email a validar
            
        Returns:
            bool: True si el formato es válido
            
        Raises:
            ValidationError: Si el formato es inválido
        """
        if not email:
            raise ValidationError("El email es requerido")
            
        # Patrón regex para validar email
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(patron, email):
            raise ValidationError("El formato del email es inválido")
        
        return True
    
    @staticmethod
    def validar_email_unico(email, excluir_usuario_id=None):
        """
        Valida que el email no esté registrado por otro usuario.
        
        Args:
            email (str): Email a validar
            excluir_usuario_id (int, optional): ID del usuario a excluir de la validación 
                                                 (útil para ediciones)
            
        Returns:
            bool: True si el email es único
            
        Raises:
            ValidationError: Si el email ya existe
        """
        query = Usuario.objects.filter(email=email)
        
        # Si estamos editando, excluir el usuario actual
        if excluir_usuario_id:
            query = query.exclude(id=excluir_usuario_id)
        
        if query.exists():
            raise ValidationError("Ya existe un usuario registrado con este email")
        
        return True
    
    @staticmethod
    def validar_contrasena_segura(password):
        """
        Valida que la contraseña cumpla con criterios de seguridad.
        Utiliza los validadores de Django más validaciones personalizadas.
        
        Args:
            password (str): Contraseña a validar
            
        Returns:
            bool: True si la contraseña es segura
            
        Raises:
            ValidationError: Si la contraseña no cumple los criterios
        """
        if not password:
            raise ValidationError("La contraseña es requerida")
        
        # Validaciones de Django (longitud mínima, no muy común, etc.)
        try:
            django_validate_password(password)
        except ValidationError as e:
            # Re-lanzar con mensajes en español
            mensajes = []
            for error in e.messages:
                mensajes.append(error)
            raise ValidationError(mensajes)
        
        # Validaciones personalizadas adicionales
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("La contraseña debe contener al menos una letra mayúscula")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("La contraseña debe contener al menos una letra minúscula")
        
        if not re.search(r'[0-9]', password):
            raise ValidationError("La contraseña debe contener al menos un número")
        
        return True
    
    @staticmethod
    def validar_telefono(telefono):
        """
        Valida que el teléfono tenga un formato válido.
        
        Args:
            telefono (str): Teléfono a validar
            
        Returns:
            bool: True si el formato es válido
            
        Raises:
            ValidationError: Si el formato es inválido
        """
        if not telefono:
            return True  # El teléfono es opcional
        
        # Permitir números, espacios, guiones y paréntesis
        patron = r'^[\d\s\-\(\)\+]+$'
        if not re.match(patron, telefono):
            raise ValidationError("El formato del teléfono es inválido")
        
        # Validar longitud (entre 7 y 20 caracteres)
        telefono_limpio = re.sub(r'[\s\-\(\)\+]', '', telefono)
        if len(telefono_limpio) < 7 or len(telefono_limpio) > 20:
            raise ValidationError("El teléfono debe tener entre 7 y 20 dígitos")
        
        return True
    
    @staticmethod
    def validar_datos_completos_profesional(datos):
        """
        Valida que un profesional tenga todos los datos requeridos.
        
        Args:
            datos (dict): Diccionario con los datos del profesional
            
        Returns:
            bool: True si los datos son completos
            
        Raises:
            ValidationError: Si faltan datos requeridos
        """
        campos_requeridos = ['servicios', 'horarios']
        errores = []
        
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo '{campo}' es requerido para profesionales")
        
        if errores:
            raise ValidationError(errores)
        
        return True
    
    @staticmethod
    def validar_horarios(horarios):
        """
        Valida que los horarios tengan el formato correcto y sean lógicos.
        
        Args:
            horarios (list): Lista de diccionarios con horarios
            
        Returns:
            bool: True si los horarios son válidos
            
        Raises:
            ValidationError: Si los horarios son inválidos
        """
        if not horarios or len(horarios) == 0:
            raise ValidationError("Debe especificar al menos un horario de disponibilidad")
        
        dias_validos = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        
        for horario in horarios:
            # Validar que tenga todos los campos
            if 'dia' not in horario or 'hora_inicio' not in horario or 'hora_fin' not in horario:
                raise ValidationError("Cada horario debe tener día, hora_inicio y hora_fin")
            
            # Validar que el día sea válido
            if horario['dia'] not in dias_validos:
                raise ValidationError(f"Día inválido: {horario['dia']}")
            
            # Validar que hora_inicio sea menor que hora_fin
            # Asumimos formato HH:MM
            try:
                hora_inicio = horario['hora_inicio']
                hora_fin = horario['hora_fin']
                
                if hora_inicio >= hora_fin:
                    raise ValidationError(
                        f"La hora de inicio debe ser menor que la hora de fin para {horario['dia']}"
                    )
            except (KeyError, TypeError):
                raise ValidationError("Formato de hora inválido")
        
        return True


class PerfilValidator:
    """
    Validador para operaciones sobre perfiles de usuario.
    """
    
    @staticmethod
    def puede_eliminar_perfil(usuario):
        """
        Valida si un usuario puede eliminar su perfil.
        No puede eliminar si tiene turnos activos/pendientes o pagos abiertos.
        
        Args:
            usuario (Usuario): Usuario que intenta eliminar su perfil
            
        Returns:
            tuple: (bool, str) - (puede_eliminar, mensaje_error)
        """
        # Importar aquí para evitar importaciones circulares
        from apps.turnos.models import Turno, Pago
        
        # Verificar turnos activos o pendientes
        if usuario.is_cliente():
            turnos_activos = Turno.objects.filter(
                cliente=usuario.perfil_cliente,
                estado__in=['pendiente', 'confirmado', 'en_curso']
            ).exists()
            
            if turnos_activos:
                return False, "No puede eliminar su perfil porque tiene turnos activos o pendientes"
        
        elif usuario.is_profesional():
            turnos_activos = Turno.objects.filter(
                profesional=usuario.perfil_profesional,
                estado__in=['pendiente', 'confirmado', 'en_curso']
            ).exists()
            
            if turnos_activos:
                return False, "No puede eliminar su perfil porque tiene turnos activos o pendientes"
        
        # Verificar pagos pendientes
        if usuario.is_cliente():
            pagos_pendientes = Pago.objects.filter(
                turno__cliente=usuario.perfil_cliente,
                estado='pendiente'
            ).exists()
            
            if pagos_pendientes:
                return False, "No puede eliminar su perfil porque tiene pagos pendientes"
        
        elif usuario.is_profesional():
            pagos_pendientes = Pago.objects.filter(
                turno__profesional=usuario.perfil_profesional,
                estado='pendiente'
            ).exists()
            
            if pagos_pendientes:
                return False, "No puede eliminar su perfil porque tiene pagos pendientes"
        
        return True, None
