"""
API Views para Reportes, Estadísticas y Búsqueda de Promociones
Implementa endpoints para CU-16, CU-30, CU-31, CU-40
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import logging

from apps.usuarios.permissions import IsAdministrador
from apps.promociones.models import Promocion
from apps.promociones.serializers import PromocionSerializer
from .models import Reporte
from .serializers import (
    EstadisticasRequestSerializer,
    ReporteClientesRequestSerializer,
    ReporteProfesionalesRequestSerializer,
    PromocionBusquedaRequestSerializer,
    PromocionBusquedaSerializer,
    ReporteSerializer,
    ReporteListSerializer
)
from .services import (
    EstadisticasService,
    ReportesService,
    PromocionBusquedaService
)

logger = logging.getLogger(__name__)


class EstadisticasPagination(PageNumberPagination):
    """Paginación personalizada para reportes"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class EstadisticasAPIView(APIView):
    """
    API para consultar estadísticas del sistema (CU-16)
    
    GET /api/estadisticas/
    - Consulta estadísticas según tipo y período
    - Query params: tipo, periodo, fecha_inicio, fecha_fin
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request):
        """
        Consulta estadísticas del sistema.
        
        Query Parameters:
        - tipo: 'usuarios', 'servicios', 'ingresos', 'calificaciones' (requerido)
        - periodo: 'mes', 'trimestre', 'anio', 'personalizado' (default: 'mes')
        - fecha_inicio: Fecha ISO 8601 (requerido si periodo='personalizado')
        - fecha_fin: Fecha ISO 8601 (requerido si periodo='personalizado')
        
        Ejemplo:
        GET /api/estadisticas/?tipo=usuarios&periodo=mes
        GET /api/estadisticas/?tipo=ingresos&periodo=personalizado&fecha_inicio=2025-01-01T00:00:00Z&fecha_fin=2025-03-31T23:59:59Z
        """
        try:
            # Validar parámetros
            serializer = EstadisticasRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                logger.warning(f"Parámetros inválidos: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Parámetros inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            datos = serializer.validated_data
            
            # Consultar estadísticas
            logger.info(f"Admin {request.user.username} consultando estadísticas tipo {datos['tipo']}")
            
            estadisticas = EstadisticasService.consultar_estadisticas(
                tipo=datos['tipo'],
                periodo=datos.get('periodo', 'mes'),
                fecha_inicio=datos.get('fecha_inicio'),
                fecha_fin=datos.get('fecha_fin')
            )
            
            return Response({
                'success': True,
                'tipo': datos['tipo'],
                'data': estadisticas
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error al consultar estadísticas: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al consultar estadísticas. Por favor, intente nuevamente.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReporteClientesAPIView(APIView):
    """
    API para generar reporte de preferencias y comportamientos de clientes (CU-31)
    
    GET /api/reportes/clientes/
    - Genera análisis detallado de clientes
    - Query params: fecha_inicio, fecha_fin, guardar
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request):
        """
        Genera reporte de preferencias de clientes.
        
        Query Parameters:
        - fecha_inicio: Fecha ISO 8601 (opcional, default: hace 90 días)
        - fecha_fin: Fecha ISO 8601 (opcional, default: hoy)
        - guardar: boolean (opcional, default: false) - Si es true, guarda el reporte en BD
        
        Ejemplo:
        GET /api/reportes/clientes/
        GET /api/reportes/clientes/?fecha_inicio=2025-01-01T00:00:00Z&fecha_fin=2025-03-31T23:59:59Z&guardar=true
        """
        try:
            # Validar parámetros
            serializer = ReporteClientesRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                logger.warning(f"Parámetros inválidos: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Parámetros inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            datos = serializer.validated_data
            
            # Generar reporte
            logger.info(f"Admin {request.user.username} generando reporte de clientes")
            
            reporte_datos = ReportesService.reporte_preferencias_clientes(
                fecha_inicio=datos.get('fecha_inicio'),
                fecha_fin=datos.get('fecha_fin')
            )
            
            # Guardar si se solicitó
            reporte_guardado = None
            if datos.get('guardar', False):
                reporte_guardado = ReportesService.guardar_reporte(
                    tipo='preferencias_cliente',
                    datos=reporte_datos,
                    usuario=request.user
                )
                logger.info(f"Reporte guardado con ID {reporte_guardado.id}")
            
            response_data = {
                'success': True,
                'message': 'Reporte generado exitosamente',
                'data': reporte_datos
            }
            
            if reporte_guardado:
                response_data['reporte_id'] = reporte_guardado.id
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error al generar reporte de clientes: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al generar el reporte. Por favor, intente nuevamente.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReporteProfesionalesAPIView(APIView):
    """
    API para generar reporte de desempeño de profesionales (CU-30)
    
    GET /api/reportes/profesionales/
    - Genera análisis detallado de profesionales
    - Query params: fecha_inicio, fecha_fin, servicio_id, calificacion_min, antiguedad_min, guardar
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request):
        """
        Genera reporte de desempeño de profesionales.
        
        Query Parameters:
        - fecha_inicio: Fecha ISO 8601 (opcional, default: hace 90 días)
        - fecha_fin: Fecha ISO 8601 (opcional, default: hoy)
        - servicio_id: ID del servicio para filtrar (opcional)
        - calificacion_min: Calificación mínima 1-5 (opcional)
        - antiguedad_min: Antigüedad mínima en días (opcional)
        - guardar: boolean (opcional, default: false) - Si es true, guarda el reporte en BD
        
        Ejemplo:
        GET /api/reportes/profesionales/
        GET /api/reportes/profesionales/?calificacion_min=4.5&servicio_id=3&guardar=true
        """
        try:
            # Validar parámetros
            serializer = ReporteProfesionalesRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                logger.warning(f"Parámetros inválidos: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Parámetros inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            datos = serializer.validated_data
            
            # Construir filtros
            filtros = {}
            if 'servicio_id' in datos and datos['servicio_id']:
                filtros['servicio_id'] = datos['servicio_id']
            if 'calificacion_min' in datos and datos['calificacion_min']:
                filtros['calificacion_min'] = datos['calificacion_min']
            if 'antiguedad_min' in datos and datos['antiguedad_min']:
                filtros['antiguedad_min'] = datos['antiguedad_min']
            
            # Generar reporte
            logger.info(f"Admin {request.user.username} generando reporte de profesionales")
            
            reporte_datos = ReportesService.reporte_profesionales(
                fecha_inicio=datos.get('fecha_inicio'),
                fecha_fin=datos.get('fecha_fin'),
                filtros=filtros
            )
            
            # Guardar si se solicitó
            reporte_guardado = None
            if datos.get('guardar', False):
                reporte_guardado = ReportesService.guardar_reporte(
                    tipo='profesionales',
                    datos=reporte_datos,
                    usuario=request.user
                )
                logger.info(f"Reporte guardado con ID {reporte_guardado.id}")
            
            response_data = {
                'success': True,
                'message': 'Reporte generado exitosamente',
                'data': reporte_datos
            }
            
            if reporte_guardado:
                response_data['reporte_id'] = reporte_guardado.id
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error al generar reporte de profesionales: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al generar el reporte. Por favor, intente nuevamente.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PromocionBusquedaAPIView(APIView):
    """
    API para búsqueda de promociones (CU-40)
    
    GET /api/promociones/buscar/
    - Busca promociones por múltiples criterios
    - Query params: nombre, estado, fecha_inicio, fecha_fin
    - Soporta paginación
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    pagination_class = EstadisticasPagination
    
    def get(self, request):
        """
        Busca promociones por criterios múltiples.
        
        Query Parameters:
        - nombre: Texto a buscar en título, descripción o código (opcional)
        - estado: 'activa' o 'inactiva' (opcional)
        - fecha_inicio: Inicio del rango de vigencia ISO 8601 (opcional)
        - fecha_fin: Fin del rango de vigencia ISO 8601 (opcional)
        - page: Número de página (opcional, default: 1)
        - page_size: Tamaño de página (opcional, default: 50, max: 100)
        
        Ejemplo:
        GET /api/promociones/buscar/?nombre=verano
        GET /api/promociones/buscar/?estado=activa&fecha_inicio=2025-01-01T00:00:00Z
        """
        try:
            # Validar parámetros
            serializer = PromocionBusquedaRequestSerializer(data=request.query_params)
            if not serializer.is_valid():
                logger.warning(f"Parámetros inválidos: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Parámetros inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            datos = serializer.validated_data
            
            # Buscar promociones
            logger.info(f"Admin {request.user.username} buscando promociones")
            
            promociones = PromocionBusquedaService.buscar_promociones(
                nombre=datos.get('nombre'),
                estado=datos.get('estado'),
                fecha_inicio=datos.get('fecha_inicio'),
                fecha_fin=datos.get('fecha_fin')
            )
            
            # Aplicar paginación
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(promociones, request)
            
            if page is not None:
                serializer = PromocionBusquedaSerializer(page, many=True)
                return paginator.get_paginated_response({
                    'success': True,
                    'message': f'{promociones.count()} promociones encontradas',
                    'filtros_aplicados': datos,
                    'results': serializer.data
                })
            
            # Sin paginación
            serializer = PromocionBusquedaSerializer(promociones, many=True)
            return Response({
                'success': True,
                'message': f'{promociones.count()} promociones encontradas',
                'filtros_aplicados': datos,
                'count': promociones.count(),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error al buscar promociones: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al buscar promociones. Por favor, intente nuevamente.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PromocionDetalleAPIView(APIView):
    """
    API para obtener detalle completo de una promoción (CU-40)
    
    GET /api/promociones/:id/detalle/
    - Obtiene información completa de una promoción
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request, id):
        """
        Obtiene información completa de una promoción.
        
        Incluye: nombre, descripción, descuento, estado, fechas,
        categoría asociada y servicios aplicables.
        """
        try:
            logger.info(f"Admin {request.user.username} consultando promoción ID {id}")
            
            promocion = get_object_or_404(Promocion, id=id)
            serializer = PromocionSerializer(promocion)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al obtener promoción: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al obtener la promoción.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportesListAPIView(APIView):
    """
    API para listar reportes guardados
    
    GET /api/reportes/
    - Lista todos los reportes generados
    - Soporta filtros y paginación
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    pagination_class = EstadisticasPagination
    
    def get(self, request):
        """
        Lista reportes guardados con filtros opcionales.
        
        Query Parameters:
        - tipo: Tipo de reporte (opcional)
        - page: Número de página (opcional)
        - page_size: Tamaño de página (opcional)
        """
        try:
            reportes = Reporte.objects.all()
            
            # Filtro por tipo
            tipo = request.query_params.get('tipo')
            if tipo:
                reportes = reportes.filter(tipo=tipo)
            
            # Aplicar paginación
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(reportes, request)
            
            if page is not None:
                serializer = ReporteListSerializer(page, many=True)
                return paginator.get_paginated_response({
                    'success': True,
                    'results': serializer.data
                })
            
            serializer = ReporteListSerializer(reportes, many=True)
            return Response({
                'success': True,
                'count': reportes.count(),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al listar reportes: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al listar reportes.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReporteDetalleAPIView(APIView):
    """
    API para obtener detalle de un reporte guardado
    
    GET /api/reportes/:id/
    - Obtiene datos completos de un reporte
    """
    permission_classes = [IsAuthenticated, IsAdministrador]
    
    def get(self, request, id):
        """Obtiene el detalle completo de un reporte guardado"""
        try:
            reporte = get_object_or_404(Reporte, id=id)
            serializer = ReporteSerializer(reporte)
            
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al obtener reporte: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al obtener el reporte.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
