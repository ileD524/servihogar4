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
