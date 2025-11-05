"""
Servicio de Estadísticas y Reportes
Implementa la lógica de negocio para CU-16, CU-30, CU-31
"""
from django.db.models import Count, Avg, Sum, Q, F
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from collections import defaultdict
import logging

from apps.usuarios.models import Usuario, Cliente, Profesional
from apps.servicios.models import Servicio, Categoria
from apps.turnos.models import Turno, Calificacion
from apps.promociones.models import Promocion
from .models import Reporte

logger = logging.getLogger(__name__)


class EstadisticasService:
    """Servicio para generar estadísticas del sistema (CU-16)"""
    
    # Períodos predefinidos
    PERIODO_MES = 'mes'
    PERIODO_TRIMESTRE = 'trimestre'
    PERIODO_ANIO = 'anio'
    PERIODO_PERSONALIZADO = 'personalizado'
    
    @staticmethod
    def obtener_rango_fechas(periodo, fecha_inicio=None, fecha_fin=None):
        """
        Calcula el rango de fechas según el período solicitado.
        
        Args:
            periodo: Tipo de período ('mes', 'trimestre', 'anio', 'personalizado')
            fecha_inicio: Fecha inicio para período personalizado
            fecha_fin: Fecha fin para período personalizado
            
        Returns:
            tuple: (fecha_inicio, fecha_fin)
        """
        now = timezone.now()
        
        if periodo == EstadisticasService.PERIODO_MES:
            fecha_inicio = now - timedelta(days=30)
            fecha_fin = now
        elif periodo == EstadisticasService.PERIODO_TRIMESTRE:
            fecha_inicio = now - timedelta(days=90)
            fecha_fin = now
        elif periodo == EstadisticasService.PERIODO_ANIO:
            fecha_inicio = now - timedelta(days=365)
            fecha_fin = now
        elif periodo == EstadisticasService.PERIODO_PERSONALIZADO:
            if not fecha_inicio or not fecha_fin:
                raise ValueError("Para período personalizado se requieren fecha_inicio y fecha_fin")
            if fecha_inicio > fecha_fin:
                raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")
        else:
            raise ValueError(f"Período inválido: {periodo}")
        
        logger.info(f"Rango de fechas calculado: {fecha_inicio} - {fecha_fin}")
        return fecha_inicio, fecha_fin
    
    @staticmethod
    def estadisticas_usuarios(fecha_inicio, fecha_fin):
        """
        Genera estadísticas de usuarios.
        
        Returns:
            dict: Estadísticas de usuarios
        """
        try:
            # Total de usuarios por rol
            total_usuarios = Usuario.objects.filter(
                date_joined__range=(fecha_inicio, fecha_fin)
            ).count()
            
            usuarios_por_rol = Usuario.objects.filter(
                date_joined__range=(fecha_inicio, fecha_fin)
            ).values('rol').annotate(
                cantidad=Count('id')
            ).order_by('-cantidad')
            
            # Usuarios activos (que tienen turnos)
            usuarios_activos = Usuario.objects.filter(
                Q(cliente__turnos__fecha_solicitud__range=(fecha_inicio, fecha_fin)) |
                Q(profesional__turnos__fecha_solicitud__range=(fecha_inicio, fecha_fin))
            ).distinct().count()
            
            # Nuevos registros en el período
            nuevos_usuarios = Usuario.objects.filter(
                date_joined__range=(fecha_inicio, fecha_fin)
            ).count()
            
            # Distribución por fecha (últimos 30 días del rango)
            usuarios_por_dia = Usuario.objects.filter(
                date_joined__range=(fecha_inicio, fecha_fin)
            ).annotate(
                dia=TruncDay('date_joined')
            ).values('dia').annotate(
                cantidad=Count('id')
            ).order_by('dia')
            
            estadisticas = {
                'total_usuarios': total_usuarios,
                'usuarios_por_rol': list(usuarios_por_rol),
                'usuarios_activos': usuarios_activos,
                'nuevos_usuarios': nuevos_usuarios,
                'usuarios_por_dia': list(usuarios_por_dia),
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                }
            }
            
            logger.info(f"Estadísticas de usuarios generadas: {total_usuarios} usuarios")
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error al generar estadísticas de usuarios: {str(e)}")
            raise
    
    @staticmethod
    def estadisticas_servicios(fecha_inicio, fecha_fin):
        """
        Genera estadísticas de servicios.
        
        Returns:
            dict: Estadísticas de servicios
        """
        try:
            # Total de servicios registrados
            total_servicios = Servicio.objects.filter(activo=True).count()
            
            # Servicios más solicitados
            servicios_populares = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).values(
                'servicio__id',
                'servicio__nombre',
                'servicio__categoria__nombre'
            ).annotate(
                cantidad_solicitudes=Count('id'),
                calificacion_promedio=Avg('calificacion__puntuacion')
            ).order_by('-cantidad_solicitudes')[:10]
            
            # Servicios por categoría
            servicios_por_categoria = Servicio.objects.filter(
                activo=True
            ).values(
                'categoria__nombre'
            ).annotate(
                cantidad=Count('id')
            ).order_by('-cantidad')
            
            # Turnos por estado
            turnos_por_estado = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).values('estado').annotate(
                cantidad=Count('id')
            ).order_by('-cantidad')
            
            # Turnos completados
            turnos_completados = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin),
                estado='completado'
            ).count()
            
            # Tasa de completitud
            total_turnos = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).count()
            
            tasa_completitud = (turnos_completados / total_turnos * 100) if total_turnos > 0 else 0
            
            estadisticas = {
                'total_servicios': total_servicios,
                'servicios_populares': list(servicios_populares),
                'servicios_por_categoria': list(servicios_por_categoria),
                'turnos_por_estado': list(turnos_por_estado),
                'total_turnos': total_turnos,
                'turnos_completados': turnos_completados,
                'tasa_completitud': round(tasa_completitud, 2),
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                }
            }
            
            logger.info(f"Estadísticas de servicios generadas: {total_turnos} turnos")
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error al generar estadísticas de servicios: {str(e)}")
            raise
    
    @staticmethod
    def estadisticas_ingresos(fecha_inicio, fecha_fin):
        """
        Genera estadísticas de ingresos.
        
        Returns:
            dict: Estadísticas financieras
        """
        try:
            # Ingresos totales de turnos completados
            turnos_completados = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin),
                estado='completado'
            )
            
            ingresos_totales = turnos_completados.aggregate(
                total=Sum('precio_final')
            )['total'] or Decimal('0.00')
            
            # Ingresos por mes
            ingresos_por_mes = turnos_completados.annotate(
                mes=TruncMonth('fecha_solicitud')
            ).values('mes').annotate(
                total=Sum('precio_final'),
                cantidad_turnos=Count('id')
            ).order_by('mes')
            
            # Ingresos por categoría de servicio
            ingresos_por_categoria = turnos_completados.values(
                'servicio__categoria__nombre'
            ).annotate(
                total=Sum('precio_final'),
                cantidad=Count('id')
            ).order_by('-total')
            
            # Ticket promedio
            ticket_promedio = turnos_completados.aggregate(
                promedio=Avg('precio_final')
            )['promedio'] or Decimal('0.00')
            
            # Profesionales top por ingresos
            profesionales_top = turnos_completados.values(
                'profesional__usuario__username',
                'profesional__usuario__first_name',
                'profesional__usuario__last_name'
            ).annotate(
                ingresos=Sum('precio_final'),
                cantidad_turnos=Count('id')
            ).order_by('-ingresos')[:10]
            
            estadisticas = {
                'ingresos_totales': float(ingresos_totales),
                'ingresos_por_mes': [
                    {
                        'mes': item['mes'].isoformat() if item['mes'] else None,
                        'total': float(item['total']),
                        'cantidad_turnos': item['cantidad_turnos']
                    }
                    for item in ingresos_por_mes
                ],
                'ingresos_por_categoria': [
                    {
                        'categoria': item['servicio__categoria__nombre'],
                        'total': float(item['total']),
                        'cantidad': item['cantidad']
                    }
                    for item in ingresos_por_categoria
                ],
                'ticket_promedio': float(ticket_promedio),
                'profesionales_top': list(profesionales_top),
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                }
            }
            
            logger.info(f"Estadísticas de ingresos generadas: ${ingresos_totales}")
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error al generar estadísticas de ingresos: {str(e)}")
            raise
    
    @staticmethod
    def estadisticas_calificaciones(fecha_inicio, fecha_fin):
        """
        Genera estadísticas de calificaciones.
        
        Returns:
            dict: Estadísticas de satisfacción
        """
        try:
            # Calificación promedio general
            calificaciones = Calificacion.objects.filter(
                fecha_calificacion__range=(fecha_inicio, fecha_fin)
            )
            
            calificacion_promedio = calificaciones.aggregate(
                promedio=Avg('puntuacion')
            )['promedio'] or 0
            
            # Distribución de calificaciones
            distribucion = calificaciones.values('puntuacion').annotate(
                cantidad=Count('id')
            ).order_by('puntuacion')
            
            # Calificaciones por servicio
            por_servicio = calificaciones.values(
                'turno__servicio__nombre'
            ).annotate(
                promedio=Avg('puntuacion'),
                cantidad=Count('id')
            ).order_by('-promedio')[:10]
            
            # Profesionales mejor calificados
            profesionales_mejor = calificaciones.values(
                'turno__profesional__usuario__username',
                'turno__profesional__usuario__first_name',
                'turno__profesional__usuario__last_name'
            ).annotate(
                promedio=Avg('puntuacion'),
                cantidad=Count('id')
            ).filter(cantidad__gte=3).order_by('-promedio')[:10]
            
            # Total de calificaciones
            total_calificaciones = calificaciones.count()
            
            estadisticas = {
                'calificacion_promedio': round(float(calificacion_promedio), 2),
                'total_calificaciones': total_calificaciones,
                'distribucion': list(distribucion),
                'por_servicio': list(por_servicio),
                'profesionales_mejor': list(profesionales_mejor),
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                }
            }
            
            logger.info(f"Estadísticas de calificaciones generadas: promedio {calificacion_promedio}")
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error al generar estadísticas de calificaciones: {str(e)}")
            raise
    
    @staticmethod
    def consultar_estadisticas(tipo, periodo='mes', fecha_inicio=None, fecha_fin=None):
        """
        Método principal para consultar estadísticas (CU-16).
        
        Args:
            tipo: Tipo de estadística ('usuarios', 'servicios', 'ingresos', 'calificaciones')
            periodo: Período de análisis
            fecha_inicio: Fecha inicio personalizada
            fecha_fin: Fecha fin personalizada
            
        Returns:
            dict: Estadísticas solicitadas
        """
        try:
            # Obtener rango de fechas
            fecha_inicio, fecha_fin = EstadisticasService.obtener_rango_fechas(
                periodo, fecha_inicio, fecha_fin
            )
            
            # Generar estadísticas según tipo
            if tipo == 'usuarios':
                return EstadisticasService.estadisticas_usuarios(fecha_inicio, fecha_fin)
            elif tipo == 'servicios':
                return EstadisticasService.estadisticas_servicios(fecha_inicio, fecha_fin)
            elif tipo == 'ingresos':
                return EstadisticasService.estadisticas_ingresos(fecha_inicio, fecha_fin)
            elif tipo == 'calificaciones':
                return EstadisticasService.estadisticas_calificaciones(fecha_inicio, fecha_fin)
            else:
                raise ValueError(f"Tipo de estadística inválido: {tipo}")
                
        except Exception as e:
            logger.error(f"Error al consultar estadísticas tipo {tipo}: {str(e)}")
            raise


class ReportesService:
    """Servicio para generar reportes especializados (CU-30, CU-31)"""
    
    @staticmethod
    def reporte_preferencias_clientes(fecha_inicio=None, fecha_fin=None, filtros=None):
        """
        Genera reporte de preferencias y comportamientos de clientes (CU-31).
        
        Args:
            fecha_inicio: Fecha inicio del análisis
            fecha_fin: Fecha fin del análisis
            filtros: Filtros adicionales
            
        Returns:
            dict: Reporte detallado de clientes
        """
        try:
            # Usar último trimestre si no se especifican fechas
            if not fecha_inicio or not fecha_fin:
                fecha_fin = timezone.now()
                fecha_inicio = fecha_fin - timedelta(days=90)
            
            logger.info(f"Generando reporte de clientes: {fecha_inicio} - {fecha_fin}")
            
            # Servicios más solicitados por cliente
            servicios_por_cliente = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).values(
                'cliente__usuario__username',
                'cliente__usuario__first_name',
                'cliente__usuario__last_name',
                'servicio__nombre',
                'servicio__categoria__nombre'
            ).annotate(
                cantidad=Count('id')
            ).order_by('cliente__usuario__username', '-cantidad')
            
            # Análisis de frecuencia horaria
            turnos_por_hora = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).extra(
                select={'hora_turno': 'EXTRACT(hour FROM hora)'}
            ).values('hora_turno').annotate(
                cantidad=Count('id')
            ).order_by('hora_turno')
            
            # Hábitos de reserva (día de la semana)
            turnos_por_dia_semana = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).extra(
                select={'dia_semana': 'EXTRACT(dow FROM fecha)'}
            ).values('dia_semana').annotate(
                cantidad=Count('id')
            ).order_by('dia_semana')
            
            # Análisis de cancelaciones
            tasa_cancelacion = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).aggregate(
                total=Count('id'),
                cancelados=Count('id', filter=Q(estado='cancelado'))
            )
            
            tasa_cancelacion_pct = (
                (tasa_cancelacion['cancelados'] / tasa_cancelacion['total'] * 100)
                if tasa_cancelacion['total'] > 0 else 0
            )
            
            # Clientes por frecuencia de uso
            clientes_frecuentes = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            ).values(
                'cliente__usuario__username',
                'cliente__usuario__first_name',
                'cliente__usuario__last_name'
            ).annotate(
                cantidad_turnos=Count('id'),
                gasto_total=Sum('precio_final'),
                servicios_distintos=Count('servicio', distinct=True)
            ).order_by('-cantidad_turnos')
            
            # Segmentación de clientes
            segmentacion = {
                'muy_activos': clientes_frecuentes.filter(cantidad_turnos__gte=10).count(),
                'activos': clientes_frecuentes.filter(
                    cantidad_turnos__gte=5, cantidad_turnos__lt=10
                ).count(),
                'ocasionales': clientes_frecuentes.filter(
                    cantidad_turnos__gte=2, cantidad_turnos__lt=5
                ).count(),
                'nuevos': clientes_frecuentes.filter(cantidad_turnos=1).count()
            }
            
            reporte = {
                'tipo': 'preferencias_clientes',
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                },
                'servicios_por_cliente': list(servicios_por_cliente[:50]),  # Top 50
                'frecuencia_horaria': list(turnos_por_hora),
                'dias_semana_populares': list(turnos_por_dia_semana),
                'tasa_cancelacion': round(tasa_cancelacion_pct, 2),
                'clientes_frecuentes': [
                    {
                        'username': c['cliente__usuario__username'],
                        'nombre': f"{c['cliente__usuario__first_name']} {c['cliente__usuario__last_name']}",
                        'cantidad_turnos': c['cantidad_turnos'],
                        'gasto_total': float(c['gasto_total'] or 0),
                        'servicios_distintos': c['servicios_distintos']
                    }
                    for c in clientes_frecuentes[:20]
                ],
                'segmentacion': segmentacion,
                'total_clientes_analizados': clientes_frecuentes.count()
            }
            
            logger.info(f"Reporte de clientes generado: {clientes_frecuentes.count()} clientes")
            return reporte
            
        except Exception as e:
            logger.error(f"Error al generar reporte de clientes: {str(e)}")
            raise
    
    @staticmethod
    def reporte_profesionales(fecha_inicio=None, fecha_fin=None, filtros=None):
        """
        Genera reporte de desempeño de profesionales (CU-30).
        
        Args:
            fecha_inicio: Fecha inicio del análisis
            fecha_fin: Fecha fin del análisis
            filtros: Dict con filtros opcionales (servicio_id, calificacion_min, antiguedad_min)
            
        Returns:
            dict: Reporte detallado de profesionales
        """
        try:
            # Usar último trimestre si no se especifican fechas
            if not fecha_inicio or not fecha_fin:
                fecha_fin = timezone.now()
                fecha_inicio = fecha_fin - timedelta(days=90)
            
            filtros = filtros or {}
            logger.info(f"Generando reporte de profesionales: {fecha_inicio} - {fecha_fin}")
            
            # Query base de turnos en el período
            turnos_query = Turno.objects.filter(
                fecha_solicitud__range=(fecha_inicio, fecha_fin)
            )
            
            # Aplicar filtros
            if 'servicio_id' in filtros:
                turnos_query = turnos_query.filter(servicio_id=filtros['servicio_id'])
            
            # Estadísticas por profesional
            profesionales_stats = turnos_query.values(
                'profesional__id',
                'profesional__usuario__username',
                'profesional__usuario__first_name',
                'profesional__usuario__last_name',
                'profesional__usuario__date_joined'
            ).annotate(
                servicios_prestados=Count('id'),
                servicios_completados=Count('id', filter=Q(estado='completado')),
                calificacion_promedio=Avg('calificacion__puntuacion'),
                ingresos_generados=Sum('precio_final', filter=Q(estado='completado')),
                tasa_completitud=Count('id', filter=Q(estado='completado')) * 100.0 / Count('id')
            ).order_by('-servicios_prestados')
            
            # Filtrar por calificación mínima si se especifica
            if 'calificacion_min' in filtros:
                profesionales_stats = profesionales_stats.filter(
                    calificacion_promedio__gte=filtros['calificacion_min']
                )
            
            # Filtrar por antigüedad si se especifica (en días)
            if 'antiguedad_min' in filtros:
                fecha_minima = timezone.now() - timedelta(days=filtros['antiguedad_min'])
                profesionales_stats = profesionales_stats.filter(
                    profesional__usuario__date_joined__lte=fecha_minima
                )
            
            # Formatear resultados
            profesionales_list = []
            for prof in profesionales_stats:
                antiguedad_dias = (timezone.now() - prof['profesional__usuario__date_joined']).days
                
                profesionales_list.append({
                    'id': prof['profesional__id'],
                    'username': prof['profesional__usuario__username'],
                    'nombre_completo': f"{prof['profesional__usuario__first_name']} {prof['profesional__usuario__last_name']}",
                    'servicios_prestados': prof['servicios_prestados'],
                    'servicios_completados': prof['servicios_completados'],
                    'calificacion_promedio': round(float(prof['calificacion_promedio'] or 0), 2),
                    'ingresos_generados': float(prof['ingresos_generados'] or 0),
                    'tasa_completitud': round(float(prof['tasa_completitud'] or 0), 2),
                    'antiguedad_dias': antiguedad_dias
                })
            
            # Resumen general
            resumen = {
                'total_profesionales': len(profesionales_list),
                'servicios_totales': sum(p['servicios_prestados'] for p in profesionales_list),
                'ingresos_totales': sum(p['ingresos_generados'] for p in profesionales_list),
                'calificacion_promedio_general': round(
                    sum(p['calificacion_promedio'] for p in profesionales_list) / len(profesionales_list)
                    if profesionales_list else 0, 2
                )
            }
            
            reporte = {
                'tipo': 'profesionales',
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                },
                'filtros_aplicados': filtros,
                'resumen': resumen,
                'profesionales': profesionales_list
            }
            
            logger.info(f"Reporte de profesionales generado: {len(profesionales_list)} profesionales")
            return reporte
            
        except Exception as e:
            logger.error(f"Error al generar reporte de profesionales: {str(e)}")
            raise
    
    @staticmethod
    def guardar_reporte(tipo, datos, usuario):
        """
        Guarda un reporte generado en la base de datos.
        
        Args:
            tipo: Tipo de reporte
            datos: Datos del reporte
            usuario: Usuario que generó el reporte
            
        Returns:
            Reporte: Instancia del reporte guardado
        """
        try:
            reporte = Reporte.objects.create(
                tipo=tipo,
                titulo=f"Reporte de {tipo} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                generado_por=usuario,
                datos_json=datos
            )
            
            logger.info(f"Reporte guardado: ID {reporte.id}, tipo {tipo}")
            return reporte
            
        except Exception as e:
            logger.error(f"Error al guardar reporte: {str(e)}")
            raise


class PromocionBusquedaService:
    """Servicio para búsqueda de promociones (CU-40)"""
    
    @staticmethod
    def buscar_promociones(nombre=None, estado=None, fecha_inicio=None, fecha_fin=None):
        """
        Busca promociones según criterios múltiples (CU-40).
        
        Args:
            nombre: Texto a buscar en el título
            estado: 'activa' o 'inactiva'
            fecha_inicio: Inicio del rango de vigencia
            fecha_fin: Fin del rango de vigencia
            
        Returns:
            QuerySet: Promociones que coinciden con los criterios
        """
        try:
            logger.info(f"Búsqueda de promociones: nombre={nombre}, estado={estado}")
            
            # Query base
            query = Promocion.objects.all()
            
            # Filtro por nombre (case-insensitive, búsqueda parcial)
            if nombre:
                query = query.filter(
                    Q(titulo__icontains=nombre) |
                    Q(descripcion__icontains=nombre) |
                    Q(codigo__icontains=nombre)
                )
            
            # Filtro por estado
            if estado is not None:
                if estado == 'activa':
                    query = query.filter(activa=True)
                elif estado == 'inactiva':
                    query = query.filter(activa=False)
            
            # Filtro por rango de vigencia
            if fecha_inicio and fecha_fin:
                # Promociones que tengan alguna superposición con el rango
                query = query.filter(
                    fecha_fin__gte=fecha_inicio,
                    fecha_inicio__lte=fecha_fin
                )
            elif fecha_inicio:
                # Promociones que terminen después de fecha_inicio
                query = query.filter(fecha_fin__gte=fecha_inicio)
            elif fecha_fin:
                # Promociones que comiencen antes de fecha_fin
                query = query.filter(fecha_inicio__lte=fecha_fin)
            
            # Ordenar por fecha de creación (más recientes primero)
            query = query.select_related('categoria').prefetch_related('servicios').order_by('-fecha_creacion')
            
            logger.info(f"Búsqueda completada: {query.count()} promociones encontradas")
            return query
            
        except Exception as e:
            logger.error(f"Error en búsqueda de promociones: {str(e)}")
            raise
