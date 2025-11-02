from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q
from .models import Reporte
from apps.turnos.models import Turno, Calificacion
from apps.servicios.models import Servicio, Categoria
from apps.usuarios.models import Cliente, Profesional
from datetime import datetime, timedelta
import json


def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'


# CU-34: Generar Reporte de Preferencias y Comportamientos de Cliente
@user_passes_test(es_administrador)
def generar_reporte_preferencias_cliente(request):
    """Administrador genera reporte de preferencias y comportamiento de clientes"""
    
    # Obtener datos estadísticos
    clientes = Cliente.objects.all()
    total_clientes = clientes.count()
    
    # Servicios más solicitados
    servicios_populares = Turno.objects.values('servicio__nombre', 'servicio__categoria__nombre')\
        .annotate(total=Count('id'))\
        .order_by('-total')[:10]
    
    # Categorías más populares
    categorias_populares = Turno.objects.values('servicio__categoria__nombre')\
        .annotate(total=Count('id'))\
        .order_by('-total')[:10]
    
    # Promedio de turnos por cliente
    turnos_por_cliente = Turno.objects.values('cliente')\
        .annotate(total=Count('id'))\
        .aggregate(promedio=Avg('total'))
    
    # Clientes más activos
    clientes_activos = Turno.objects.values('cliente__usuario__first_name', 'cliente__usuario__last_name')\
        .annotate(total_turnos=Count('id'))\
        .order_by('-total_turnos')[:10]
    
    # Horarios más solicitados
    horarios_populares = Turno.objects.extra(select={'hora': 'CAST(strftime("%%H", fecha_hora) AS INTEGER)'})\
        .values('hora')\
        .annotate(total=Count('id'))\
        .order_by('-total')[:10]
    
    # Preparar datos del reporte
    datos = {
        'total_clientes': total_clientes,
        'servicios_populares': list(servicios_populares),
        'categorias_populares': list(categorias_populares),
        'promedio_turnos_por_cliente': turnos_por_cliente['promedio'] or 0,
        'clientes_activos': list(clientes_activos),
        'horarios_populares': list(horarios_populares),
        'fecha_generacion': datetime.now().isoformat()
    }
    
    # Crear registro de reporte
    reporte = Reporte.objects.create(
        tipo='preferencias_cliente',
        titulo='Reporte de Preferencias y Comportamientos de Clientes',
        descripcion=f'Reporte generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        generado_por=request.user,
        datos_json=datos
    )
    
    messages.success(request, 'Reporte generado exitosamente')
    return redirect('reportes:ver_reporte', id=reporte.id)


@user_passes_test(es_administrador)
def generar_reporte_servicios_populares(request):
    """Reporte de servicios más populares"""
    
    servicios = Servicio.objects.annotate(
        total_turnos=Count('turnos')
    ).order_by('-total_turnos')[:20]
    
    datos = {
        'servicios': [
            {
                'nombre': s.nombre,
                'categoria': s.categoria.nombre,
                'profesional': s.profesional.usuario.get_full_name(),
                'total_turnos': s.total_turnos,
                'precio_base': str(s.precio_base)
            }
            for s in servicios
        ]
    }
    
    reporte = Reporte.objects.create(
        tipo='servicios_populares',
        titulo='Reporte de Servicios Más Populares',
        descripcion=f'Reporte generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        generado_por=request.user,
        datos_json=datos
    )
    
    messages.success(request, 'Reporte generado exitosamente')
    return redirect('reportes:ver_reporte', id=reporte.id)


@user_passes_test(es_administrador)
def generar_reporte_ingresos(request):
    """Reporte de ingresos"""
    from apps.turnos.models import Pago
    
    # Últimos 12 meses
    hoy = datetime.now()
    inicio = hoy - timedelta(days=365)
    
    pagos = Pago.objects.filter(
        estado='aprobado',
        fecha_pago__gte=inicio
    )
    
    total_ingresos = pagos.aggregate(total=Sum('monto'))['total'] or 0
    
    # Ingresos por mes
    ingresos_mensuales = pagos.extra(
        select={'mes': 'strftime("%%Y-%%m", fecha_pago)'}
    ).values('mes').annotate(total=Sum('monto')).order_by('mes')
    
    # Ingresos por método de pago
    ingresos_por_metodo = pagos.values('metodo').annotate(total=Sum('monto'))
    
    datos = {
        'total_ingresos': str(total_ingresos),
        'ingresos_mensuales': list(ingresos_mensuales),
        'ingresos_por_metodo': list(ingresos_por_metodo),
        'periodo': f'{inicio.strftime("%d/%m/%Y")} - {hoy.strftime("%d/%m/%Y")}'
    }
    
    reporte = Reporte.objects.create(
        tipo='ingresos',
        titulo='Reporte de Ingresos',
        descripcion=f'Reporte generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        generado_por=request.user,
        datos_json=datos
    )
    
    messages.success(request, 'Reporte generado exitosamente')
    return redirect('reportes:ver_reporte', id=reporte.id)


@user_passes_test(es_administrador)
def generar_reporte_profesionales(request):
    """Reporte de desempeño de profesionales"""
    
    profesionales = Profesional.objects.annotate(
        total_turnos=Count('turnos'),
        turnos_completados=Count('turnos', filter=Q(turnos__estado='completado'))
    ).order_by('-total_turnos')[:20]
    
    datos = {
        'profesionales': [
            {
                'nombre': p.usuario.get_full_name(),
                'especialidades': p.especialidades,
                'total_turnos': p.total_turnos,
                'turnos_completados': p.turnos_completados,
                'calificacion_promedio': str(p.calificacion_promedio),
                'disponible': p.disponible
            }
            for p in profesionales
        ]
    }
    
    reporte = Reporte.objects.create(
        tipo='profesionales',
        titulo='Reporte de Desempeño de Profesionales',
        descripcion=f'Reporte generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        generado_por=request.user,
        datos_json=datos
    )
    
    messages.success(request, 'Reporte generado exitosamente')
    return redirect('reportes:ver_reporte', id=reporte.id)


@user_passes_test(es_administrador)
def ver_reporte(request, id):
    """Ver detalle de un reporte"""
    reporte = get_object_or_404(Reporte, id=id)
    
    # Convertir datos JSON a formato legible
    datos = reporte.datos_json
    
    return render(request, 'reportes/ver_reporte.html', {
        'reporte': reporte,
        'datos': datos
    })


@user_passes_test(es_administrador)
def listar_reportes(request):
    """Listar todos los reportes generados"""
    reportes = Reporte.objects.all().order_by('-fecha_generacion')
    return render(request, 'reportes/listar_reportes.html', {'reportes': reportes})


@user_passes_test(es_administrador)
def menu_reportes(request):
    """Menú principal de reportes"""
    return render(request, 'reportes/menu_reportes.html')
