"""
Serializers para APIs de Reportes y Estadísticas
"""
from rest_framework import serializers
from .models import Reporte
from apps.promociones.models import Promocion


class EstadisticasRequestSerializer(serializers.Serializer):
    """Serializer para validar request de estadísticas"""
    tipo = serializers.ChoiceField(
        choices=['usuarios', 'servicios', 'ingresos', 'calificaciones'],
        required=True,
        help_text="Tipo de estadística a consultar"
    )
    periodo = serializers.ChoiceField(
        choices=['mes', 'trimestre', 'anio', 'personalizado'],
        default='mes',
        help_text="Período de análisis"
    )
    fecha_inicio = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Fecha inicio para período personalizado (ISO 8601)"
    )
    fecha_fin = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Fecha fin para período personalizado (ISO 8601)"
    )
    
    def validate(self, attrs):
        """Validación cruzada de campos"""
        if attrs.get('periodo') == 'personalizado':
            if not attrs.get('fecha_inicio') or not attrs.get('fecha_fin'):
                raise serializers.ValidationError(
                    "Para período personalizado se requieren fecha_inicio y fecha_fin"
                )
            if attrs['fecha_inicio'] > attrs['fecha_fin']:
                raise serializers.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin"
                )
        return attrs


class ReporteClientesRequestSerializer(serializers.Serializer):
    """Serializer para request de reporte de clientes"""
    fecha_inicio = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Fecha inicio del período de análisis"
    )
    fecha_fin = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Fecha fin del período de análisis"
    )
    guardar = serializers.BooleanField(
        default=False,
        help_text="Si es True, guarda el reporte en la base de datos"
    )
    
    def validate(self, attrs):
        """Validación de fechas"""
        if attrs.get('fecha_inicio') and attrs.get('fecha_fin'):
            if attrs['fecha_inicio'] > attrs['fecha_fin']:
                raise serializers.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin"
                )
        return attrs


class ReporteProfesionalesRequestSerializer(serializers.Serializer):
    """Serializer para request de reporte de profesionales"""
    fecha_inicio = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Fecha inicio del período de análisis"
    )
    fecha_fin = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Fecha fin del período de análisis"
    )
    servicio_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID del servicio para filtrar"
    )
    calificacion_min = serializers.FloatField(
        required=False,
        allow_null=True,
        min_value=1.0,
        max_value=5.0,
        help_text="Calificación mínima para filtrar (1-5)"
    )
    antiguedad_min = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0,
        help_text="Antigüedad mínima en días"
    )
    guardar = serializers.BooleanField(
        default=False,
        help_text="Si es True, guarda el reporte en la base de datos"
    )
    
    def validate(self, attrs):
        """Validación de fechas"""
        if attrs.get('fecha_inicio') and attrs.get('fecha_fin'):
            if attrs['fecha_inicio'] > attrs['fecha_fin']:
                raise serializers.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin"
                )
        return attrs


class PromocionBusquedaRequestSerializer(serializers.Serializer):
    """Serializer para request de búsqueda de promociones"""
    nombre = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        help_text="Texto a buscar en título, descripción o código"
    )
    estado = serializers.ChoiceField(
        choices=['activa', 'inactiva'],
        required=False,
        allow_null=True,
        help_text="Estado de la promoción"
    )
    fecha_inicio = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Inicio del rango de vigencia"
    )
    fecha_fin = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Fin del rango de vigencia"
    )
    
    def validate(self, attrs):
        """Validación de fechas"""
        if attrs.get('fecha_inicio') and attrs.get('fecha_fin'):
            if attrs['fecha_inicio'] > attrs['fecha_fin']:
                raise serializers.ValidationError(
                    "La fecha de inicio debe ser anterior a la fecha de fin"
                )
        return attrs


class PromocionBusquedaSerializer(serializers.ModelSerializer):
    """Serializer para resultados de búsqueda de promociones"""
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True,
        allow_null=True
    )
    cantidad_servicios = serializers.SerializerMethodField()
    esta_vigente = serializers.SerializerMethodField()
    tipo_descuento_display = serializers.CharField(
        source='get_tipo_descuento_display',
        read_only=True
    )
    
    class Meta:
        model = Promocion
        fields = [
            'id',
            'titulo',
            'descripcion',
            'tipo_descuento',
            'tipo_descuento_display',
            'valor_descuento',
            'categoria_nombre',
            'cantidad_servicios',
            'fecha_inicio',
            'fecha_fin',
            'activa',
            'esta_vigente',
            'codigo',
            'fecha_creacion'
        ]
    
    def get_cantidad_servicios(self, obj):
        """Retorna la cantidad de servicios asociados"""
        return obj.servicios.count()
    
    def get_esta_vigente(self, obj):
        """Indica si la promoción está vigente actualmente"""
        return obj.esta_vigente()


class ReporteSerializer(serializers.ModelSerializer):
    """Serializer para modelo Reporte"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    generado_por_username = serializers.CharField(
        source='generado_por.username',
        read_only=True
    )
    
    class Meta:
        model = Reporte
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'titulo',
            'descripcion',
            'fecha_generacion',
            'generado_por_username',
            'datos_json'
        ]
        read_only_fields = ['id', 'fecha_generacion']


class ReporteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de reportes"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    generado_por_username = serializers.CharField(
        source='generado_por.username',
        read_only=True
    )
    
    class Meta:
        model = Reporte
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'titulo',
            'fecha_generacion',
            'generado_por_username'
        ]
