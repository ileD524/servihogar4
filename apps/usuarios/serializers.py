"""
Serializers para la API REST de usuarios.
Convierte objetos Python/Django en JSON y viceversa.
"""
from rest_framework import serializers
from .models import Usuario, Cliente, Profesional, HorarioDisponibilidad
from apps.servicios.models import Servicio


class HorarioDisponibilidadSerializer(serializers.ModelSerializer):
    """Serializer para horarios de disponibilidad de profesionales"""
    
    dia_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    
    class Meta:
        model = HorarioDisponibilidad
        fields = ['id', 'dia_semana', 'dia_display', 'hora_inicio', 'hora_fin']


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer para perfil de cliente"""
    
    class Meta:
        model = Cliente
        fields = ['preferencias', 'historial_busquedas']


class ProfesionalSerializer(serializers.ModelSerializer):
    """Serializer para perfil de profesional"""
    
    horarios = HorarioDisponibilidadSerializer(many=True, read_only=True)
    servicios = serializers.SerializerMethodField()
    
    class Meta:
        model = Profesional
        fields = [
            'especialidades', 'anios_experiencia', 'certificaciones',
            'calificacion_promedio', 'disponible', 'radio_cobertura_km',
            'horarios', 'servicios'
        ]
    
    def get_servicios(self, obj):
        """Obtiene los servicios ofrecidos por el profesional"""
        from apps.servicios.models import Servicio
        servicios = Servicio.objects.filter(profesional=obj, activo=True)
        return [{'id': s.id, 'nombre': s.nombre, 'precio': str(s.precio)} for s in servicios]


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer base para Usuario.
    Incluye información del perfil según el rol.
    """
    
    perfil_cliente = ClienteSerializer(read_only=True)
    perfil_profesional = ProfesionalSerializer(read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nombre_completo', 'rol', 'rol_display', 'telefono', 'direccion',
            'foto_perfil', 'fecha_registro', 'fecha_modificacion',
            'activo', 'perfil_cliente', 'perfil_profesional'
        ]
        read_only_fields = ['id', 'fecha_registro', 'fecha_modificacion', 'activo']
    
    def get_nombre_completo(self, obj):
        """Retorna el nombre completo del usuario"""
        return obj.get_full_name()


class RegistroUsuarioSerializer(serializers.Serializer):
    """
    Serializer para registro de nuevos usuarios (CU-01).
    Validaciones integradas.
    """
    
    # Datos básicos
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    
    # Tipo de usuario
    rol = serializers.ChoiceField(choices=['cliente', 'profesional'], required=True)
    
    # Datos adicionales para profesionales
    anios_experiencia = serializers.IntegerField(required=False, default=0, min_value=0)
    servicios = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    horarios = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=False
    )
    
    def validate_password_confirm(self, value):
        """Validar que las contraseñas coincidan"""
        password = self.initial_data.get('password')
        if password != value:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return value
    
    def validate_username(self, value):
        """Validar que el username sea único"""
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso")
        return value
    
    def validate(self, data):
        """Validación adicional según el rol"""
        if data.get('rol') == 'profesional':
            # Para profesionales, validar que se proporcionen servicios y horarios
            if not data.get('servicios'):
                raise serializers.ValidationError({
                    'servicios': 'Los profesionales deben seleccionar al menos un servicio'
                })
            if not data.get('horarios'):
                raise serializers.ValidationError({
                    'horarios': 'Los profesionales deben definir sus horarios de disponibilidad'
                })
        
        return data


class ModificarPerfilSerializer(serializers.Serializer):
    """
    Serializer para modificación de perfil (CU-03).
    Permite actualizar datos básicos y específicos del rol.
    """
    
    # Datos básicos (todos opcionales en modificación)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    foto_perfil = serializers.ImageField(required=False, allow_null=True)
    
    # Datos para profesionales
    anios_experiencia = serializers.IntegerField(required=False, min_value=0)
    servicios = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    horarios = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=False
    )
    
    def validate_email(self, value):
        """Validar que el email sea único (excepto para el usuario actual)"""
        usuario = self.context.get('usuario')
        if usuario and value != usuario.email:
            if Usuario.objects.filter(email=value).exclude(id=usuario.id).exists():
                raise serializers.ValidationError("Este email ya está en uso")
        return value


class GoogleAuthSerializer(serializers.Serializer):
    """
    Serializer para autenticación con Google (CU-01).
    Recibe el código de autorización de Google.
    """
    
    code = serializers.CharField(required=True)


class CompletarDatosGoogleSerializer(serializers.Serializer):
    """
    Serializer para completar datos de usuario registrado con Google (CU-01).
    """
    
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    rol = serializers.ChoiceField(choices=['cliente', 'profesional'], required=False)
    
    # Datos adicionales para cambio a profesional
    anios_experiencia = serializers.IntegerField(required=False, default=0, min_value=0)
    servicios = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    horarios = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=False
    )
    
    def validate(self, data):
        """Validar datos según el rol"""
        if data.get('rol') == 'profesional':
            # Si cambia a profesional, validar servicios y horarios
            if not data.get('servicios'):
                raise serializers.ValidationError({
                    'servicios': 'Debe seleccionar al menos un servicio'
                })
            if not data.get('horarios'):
                raise serializers.ValidationError({
                    'horarios': 'Debe definir sus horarios de disponibilidad'
                })
        
        return data


class ConfirmarEmailSerializer(serializers.Serializer):
    """
    Serializer para confirmar email (CU-01).
    Recibe token y uidb64 para validar.
    """
    
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)


class EliminarPerfilSerializer(serializers.Serializer):
    """
    Serializer para confirmar eliminación de perfil (CU-02).
    Requiere confirmación explícita.
    """
    
    confirmar = serializers.BooleanField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text="Contraseña para confirmar (solo para usuarios con autenticación manual)"
    )
    
    def validate_confirmar(self, value):
        """Validar que se confirme explícitamente"""
        if not value:
            raise serializers.ValidationError(
                "Debe confirmar explícitamente que desea eliminar su perfil"
            )
        return value


# ============================================================================
# SERIALIZERS PARA ADMINISTRADORES (CU-04, CU-05, CU-06)
# ============================================================================

class AdminRegistroUsuarioSerializer(serializers.Serializer):
    """
    Serializer para registro de usuarios por administrador (CU-04).
    El admin puede crear usuarios directamente activos o pendientes.
    """
    
    # Datos básicos
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, 
        required=False,
        style={'input_type': 'password'},
        help_text="Opcional. Si no se proporciona, se genera una temporal"
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    
    # Tipo de usuario
    rol = serializers.ChoiceField(choices=['cliente', 'profesional'], required=True)
    
    # Estado inicial (el admin decide)
    estado = serializers.ChoiceField(
        choices=['activo', 'pendiente'],
        default='activo',
        help_text="Estado inicial del usuario"
    )
    
    # Autenticación Google
    google_id = serializers.CharField(required=False, allow_blank=True)
    
    # Datos adicionales para profesionales
    anios_experiencia = serializers.IntegerField(required=False, default=0, min_value=0)
    servicios = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False,
        help_text="IDs de servicios para profesionales"
    )
    horarios = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=False
    )
    
    def validate_username(self, value):
        """Validar que el username sea único"""
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso")
        return value
    
    def validate(self, data):
        """Validación adicional según el rol"""
        if data.get('rol') == 'profesional':
            # Para profesionales, servicios son requeridos
            if not data.get('servicios'):
                raise serializers.ValidationError({
                    'servicios': 'Los profesionales deben tener al menos un servicio asignado'
                })
        
        return data


class AdminModificarUsuarioSerializer(serializers.Serializer):
    """
    Serializer para modificación de usuarios por administrador (CU-05).
    El admin puede modificar cualquier campo, incluido el rol y estado.
    """
    
    # Datos básicos (todos opcionales)
    username = serializers.CharField(max_length=150, required=False)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    
    # El admin puede cambiar el rol
    rol = serializers.ChoiceField(
        choices=['cliente', 'profesional'],
        required=False,
        help_text="Cambiar rol requiere que no haya turnos activos"
    )
    
    # El admin puede activar/desactivar usuarios
    activo = serializers.BooleanField(
        required=False,
        help_text="Estado activo/inactivo del usuario"
    )
    
    # Datos para profesionales
    anios_experiencia = serializers.IntegerField(required=False, min_value=0)
    servicios = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    horarios = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=False
    )
    
    def validate_email(self, value):
        """Validar que el email sea único (excepto para el usuario actual)"""
        usuario_id = self.context.get('usuario_id')
        if usuario_id:
            if Usuario.objects.filter(email=value).exclude(id=usuario_id).exists():
                raise serializers.ValidationError("Este email ya está en uso")
        return value
    
    def validate_username(self, value):
        """Validar que el username sea único (excepto para el usuario actual)"""
        usuario_id = self.context.get('usuario_id')
        if usuario_id:
            if Usuario.objects.filter(username=value).exclude(id=usuario_id).exists():
                raise serializers.ValidationError("Este nombre de usuario ya está en uso")
        return value
    
    def validate(self, data):
        """Validación adicional"""
        # Si cambia a profesional, debe proporcionar servicios
        if data.get('rol') == 'profesional':
            if 'servicios' in data and not data['servicios']:
                raise serializers.ValidationError({
                    'servicios': 'Los profesionales deben tener al menos un servicio'
                })
        
        return data


class AdminEliminarUsuarioSerializer(serializers.Serializer):
    """
    Serializer para eliminación de usuarios por administrador (CU-06).
    Permite forzar la eliminación aunque haya turnos/pagos activos.
    """
    
    confirmar = serializers.BooleanField(required=True)
    forzar = serializers.BooleanField(
        default=False,
        help_text="Forzar eliminación aunque haya turnos o pagos activos (usar con precaución)"
    )
    
    def validate_confirmar(self, value):
        """Validar que se confirme explícitamente"""
        if not value:
            raise serializers.ValidationError(
                "Debe confirmar explícitamente que desea eliminar este usuario"
            )
        return value


class FiltrosUsuarioSerializer(serializers.Serializer):
    """
    Serializer para filtros de listado de usuarios.
    """
    
    rol = serializers.ChoiceField(
        choices=['cliente', 'profesional', 'administrador'],
        required=False,
        allow_blank=True
    )
    activo = serializers.BooleanField(required=False)
    busqueda = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Buscar en nombre, email, username"
    )
    orden = serializers.ChoiceField(
        choices=[
            'username', '-username',
            'email', '-email',
            'fecha_registro', '-fecha_registro',
            'first_name', '-first_name',
            'last_name', '-last_name'
        ],
        required=False,
        default='-fecha_registro'
    )
    pagina = serializers.IntegerField(min_value=1, default=1)
    por_pagina = serializers.IntegerField(min_value=1, max_value=100, default=20)


# ============================================================================
# SERIALIZERS PARA AUTENTICACIÓN (CU-07, CU-08)
# ============================================================================

class LoginEmailSerializer(serializers.Serializer):
    """
    Serializer para inicio de sesión con email y contraseña (CU-07).
    """
    
    email = serializers.EmailField(
        required=True,
        help_text="Email registrado en el sistema"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Contraseña de la cuenta"
    )
    
    def validate_email(self, value):
        """Normalizar email a minúsculas"""
        return value.lower().strip()


class LoginGoogleSerializer(serializers.Serializer):
    """
    Serializer para inicio de sesión con Google OAuth (CU-07).
    """
    
    token = serializers.CharField(
        required=True,
        help_text="Token JWT de Google OAuth obtenido desde el frontend"
    )
    
    def validate_token(self, value):
        """Validar que el token no esté vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Token de Google requerido"
            )
        return value.strip()


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para cierre de sesión (CU-08).
    """
    
    refresh_token = serializers.CharField(
        required=False,
        help_text="Refresh token JWT a invalidar (opcional)"
    )


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de tokens JWT.
    Solo para documentación.
    """
    
    access = serializers.CharField(
        read_only=True,
        help_text="Access token JWT (corta duración)"
    )
    refresh = serializers.CharField(
        read_only=True,
        help_text="Refresh token JWT (larga duración)"
    )


class UsuarioLoginResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta de login exitoso.
    Solo para documentación.
    """
    
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    rol = serializers.ChoiceField(
        choices=['administrador', 'profesional', 'cliente'],
        read_only=True
    )
    foto_perfil = serializers.URLField(read_only=True, allow_null=True)
