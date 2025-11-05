"""
Serializers para la API de Promociones
"""
from rest_framework import serializers
from .models import Promocion
from apps.servicios.models import Categoria, Servicio


class CategoriaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para Categoria"""
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']


class ServicioSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para Servicio"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'categoria_nombre']


class PromocionSerializer(serializers.ModelSerializer):
    """Serializer completo para Promocion con validaciones"""
    
    # Campos de solo lectura
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True)
    esta_vigente = serializers.SerializerMethodField()
    
    # Campos anidados para respuestas
    categoria_detalle = CategoriaSimpleSerializer(source='categoria', read_only=True)
    servicios_detalle = ServicioSimpleSerializer(source='servicios', many=True, read_only=True)
    
    # Campos para escritura
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(),
        required=False,
        allow_null=True
    )
    servicios = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Promocion
        fields = [
            'id',
            'titulo',
            'descripcion',
            'tipo_descuento',
            'valor_descuento',
            'categoria',
            'categoria_detalle',
            'servicios',
            'servicios_detalle',
            'fecha_inicio',
            'fecha_fin',
            'activa',
            'codigo',
            'fecha_creacion',
            'fecha_modificacion',
            'esta_vigente'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_modificacion']
    
    def get_esta_vigente(self, obj):
        """Indica si la promoción está vigente actualmente"""
        return obj.esta_vigente()
    
    def validate_titulo(self, value):
        """Valida que el título no esté vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError("El título de la promoción es obligatorio")
        return value.strip()
    
    def validate_tipo_descuento(self, value):
        """Valida que el tipo de descuento sea válido"""
        if value not in ['porcentaje', 'monto_fijo']:
            raise serializers.ValidationError("El tipo de descuento debe ser 'porcentaje' o 'monto_fijo'")
        return value
    
    def validate(self, attrs):
        """Validaciones a nivel de objeto"""
        # Estas validaciones se harán en el servicio para mantener
        # la lógica de negocio centralizada
        return attrs


class PromocionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de promociones"""
    
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    cantidad_servicios = serializers.SerializerMethodField()
    esta_vigente = serializers.SerializerMethodField()
    tipo_descuento_display = serializers.CharField(source='get_tipo_descuento_display', read_only=True)
    
    class Meta:
        model = Promocion
        fields = [
            'id',
            'titulo',
            'tipo_descuento',
            'tipo_descuento_display',
            'valor_descuento',
            'categoria_nombre',
            'cantidad_servicios',
            'fecha_inicio',
            'fecha_fin',
            'activa',
            'esta_vigente',
            'fecha_creacion'
        ]
    
    def get_cantidad_servicios(self, obj):
        """Retorna la cantidad de servicios asociados"""
        return obj.servicios.count()
    
    def get_esta_vigente(self, obj):
        """Indica si la promoción está vigente actualmente"""
        return obj.esta_vigente()


class PromocionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar promociones"""
    
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(),
        required=False,
        allow_null=True
    )
    servicios = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Promocion
        fields = [
            'titulo',
            'descripcion',
            'tipo_descuento',
            'valor_descuento',
            'categoria',
            'servicios',
            'fecha_inicio',
            'fecha_fin',
            'codigo'
        ]
    
    def validate_titulo(self, value):
        """Valida que el título no esté vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError("El título de la promoción es obligatorio")
        return value.strip()
    
    def validate_tipo_descuento(self, value):
        """Valida que el tipo de descuento sea válido"""
        if value not in ['porcentaje', 'monto_fijo']:
            raise serializers.ValidationError("El tipo de descuento debe ser 'porcentaje' o 'monto_fijo'")
        return value
