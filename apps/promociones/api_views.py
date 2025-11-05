"""
API Views para Promociones
Implementa endpoints RESTful para CU-18, CU-19, CU-20
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Promocion
from .serializers import (
    PromocionSerializer,
    PromocionListSerializer,
    PromocionCreateUpdateSerializer
)
from .services import PromocionService
from apps.usuarios.permissions import IsAdministrador


class PromocionListCreateAPIView(APIView):
    """
    API para listar y crear promociones
    
    GET /api/promociones/
    - Lista todas las promociones (con filtros opcionales)
    - Query params: activa, vigente
    
    POST /api/promociones/
    - Registra una nueva promoción (CU-18)
    - Requiere autenticación como administrador
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request):
        """Lista promociones con filtros opcionales"""
        promociones = Promocion.objects.all()
        
        # Filtro por estado activo
        activa = request.query_params.get('activa')
        if activa is not None:
            activa_bool = activa.lower() in ['true', '1', 'yes']
            promociones = promociones.filter(activa=activa_bool)
        
        # Filtro por vigencia actual
        vigente = request.query_params.get('vigente')
        if vigente is not None and vigente.lower() in ['true', '1', 'yes']:
            now = timezone.now()
            promociones = promociones.filter(
                activa=True,
                fecha_inicio__lte=now,
                fecha_fin__gte=now
            )
        
        serializer = PromocionListSerializer(promociones, many=True)
        return Response({
            'success': True,
            'count': promociones.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """
        Registra una nueva promoción (CU-18)
        
        Body (JSON):
        {
            "titulo": "Promoción de verano",
            "descripcion": "Descuento especial para servicios de limpieza",
            "tipo_descuento": "porcentaje",  // o "monto_fijo"
            "valor_descuento": "15.00",
            "categoria": 1,  // opcional, ID de categoría
            "servicios": [1, 2, 3],  // opcional, IDs de servicios
            "fecha_inicio": "2025-01-01T00:00:00Z",
            "fecha_fin": "2025-01-31T23:59:59Z",
            "codigo": "VERANO2025"  // opcional
        }
        """
        # Validar datos básicos con serializer
        serializer = PromocionCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Datos inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Procesar con el servicio que aplica reglas de negocio
        promocion, errores = PromocionService.registrar_promocion(serializer.validated_data)
        
        if errores:
            return Response({
                'success': False,
                'message': 'Error en validación de reglas de negocio',
                'errors': errores
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Retornar promoción creada
        response_serializer = PromocionSerializer(promocion)
        return Response({
            'success': True,
            'message': 'Promoción registrada exitosamente',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class PromocionDetailAPIView(APIView):
    """
    API para operaciones sobre una promoción específica
    
    GET /api/promociones/:id/
    - Obtiene detalles de una promoción
    
    PUT /api/promociones/:id/
    - Modifica una promoción existente (CU-19)
    - Requiere autenticación como administrador
    
    DELETE /api/promociones/:id/
    - Elimina (inactiva) una promoción (CU-20)
    - Requiere autenticación como administrador
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request, id):
        """Obtiene detalles de una promoción"""
        promocion = get_object_or_404(Promocion, id=id)
        serializer = PromocionSerializer(promocion)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, id):
        """
        Modifica una promoción existente (CU-19)
        
        Body (JSON) - todos los campos son opcionales:
        {
            "titulo": "Nuevo título",
            "descripcion": "Nueva descripción",
            "tipo_descuento": "porcentaje",
            "valor_descuento": "20.00",
            "categoria": 2,
            "servicios": [2, 3, 4],
            "fecha_inicio": "2025-02-01T00:00:00Z",
            "fecha_fin": "2025-02-28T23:59:59Z",
            "codigo": "NUEVO2025"
        }
        """
        promocion = get_object_or_404(Promocion, id=id)
        
        # Validar datos básicos con serializer
        serializer = PromocionCreateUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Datos inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Procesar con el servicio que aplica reglas de negocio
        promocion_actualizada, errores = PromocionService.modificar_promocion(
            promocion,
            serializer.validated_data
        )
        
        if errores:
            return Response({
                'success': False,
                'message': 'Error en validación de reglas de negocio',
                'errors': errores
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Retornar promoción actualizada
        response_serializer = PromocionSerializer(promocion_actualizada)
        return Response({
            'success': True,
            'message': 'Promoción modificada exitosamente',
            'data': response_serializer.data
        })
    
    def delete(self, request, id):
        """
        Elimina (inactiva) una promoción (CU-20)
        
        Solo puede eliminarse si no hay turnos activos asociados.
        La eliminación es lógica (soft delete), cambia el estado a inactivo.
        """
        promocion = get_object_or_404(Promocion, id=id)
        
        # Verificar y eliminar con el servicio
        exitoso, mensaje = PromocionService.eliminar_promocion(promocion)
        
        if not exitoso:
            return Response({
                'success': False,
                'message': mensaje
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': mensaje
        }, status=status.HTTP_200_OK)


class PromocionValidarEliminacionAPIView(APIView):
    """
    API para validar si una promoción puede ser eliminada
    
    GET /api/promociones/:id/validar-eliminacion/
    - Verifica si la promoción puede eliminarse
    - Retorna información sobre turnos activos asociados
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request, id):
        """Valida si la promoción puede eliminarse"""
        promocion = get_object_or_404(Promocion, id=id)
        
        puede_eliminar, mensaje, cantidad = PromocionService.puede_eliminar_promocion(promocion)
        
        return Response({
            'success': True,
            'puede_eliminar': puede_eliminar,
            'message': mensaje if not puede_eliminar else 'La promoción puede eliminarse',
            'turnos_activos': cantidad
        })


class PromocionVigentesAPIView(APIView):
    """
    API para obtener promociones vigentes
    
    GET /api/promociones/vigentes/
    - Lista promociones activas y vigentes en el momento actual
    - No requiere autenticación (puede ser consultado por clientes)
    """
    permission_classes = []  # Público
    
    def get(self, request):
        """Lista promociones vigentes actualmente"""
        now = timezone.now()
        promociones = Promocion.objects.filter(
            activa=True,
            fecha_inicio__lte=now,
            fecha_fin__gte=now
        )
        
        serializer = PromocionListSerializer(promociones, many=True)
        return Response({
            'success': True,
            'count': promociones.count(),
            'data': serializer.data
        })
