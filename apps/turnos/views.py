from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import Turno, Pago, Calificacion
from .forms import SolicitarTurnoForm, ModificarTurnoForm, CalificarTurnoForm, BuscarTurnoForm, ConfirmarTurnoForm
from apps.usuarios.models import Usuario, Profesional, HorarioDisponibilidad
from apps.servicios.models import Servicio
from datetime import datetime, timedelta, time
from django.utils import timezone


def es_cliente(user):
    return user.is_authenticated and user.rol == 'cliente'

def es_profesional(user):
    return user.is_authenticated and user.rol == 'profesional'


# CU-23: Solicitar Turno
@user_passes_test(es_cliente)
def solicitar_turno(request):
    """Cliente solicita un turno"""
    if request.method == 'POST':
        servicio_id = request.POST.get('servicio_id')
        servicio = None
        
        # Obtener el servicio para cargar promociones en el formulario
        if servicio_id:
            try:
                servicio = Servicio.objects.get(id=servicio_id)
            except Servicio.DoesNotExist:
                pass
        
        form = SolicitarTurnoForm(request.POST, servicio=servicio)
        
        if form.is_valid():
            # Obtener datos del formulario oculto
            profesional_id = request.POST.get('profesional_id')
            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            latitud = request.POST.get('latitud')
            longitud = request.POST.get('longitud')
            
            if not all([servicio_id, profesional_id, fecha, hora]):
                messages.error(request, 'Debe seleccionar un servicio, profesional, fecha y hora')
                return render(request, 'turnos/solicitar_turno.html', {'form': form})
            
            try:
                profesional = Profesional.objects.get(id=profesional_id)
                
                # Crear el turno
                turno = form.save(commit=False)
                turno.cliente = request.user.perfil_cliente
                turno.servicio = servicio
                turno.profesional = profesional
                turno.fecha = fecha
                turno.hora = hora
                turno.latitud = latitud if latitud else None
                turno.longitud = longitud if longitud else None
                
                # Manejar promoción
                codigo_promocion = form.cleaned_data.get('codigo_promocion')
                promocion_seleccionada = form.cleaned_data.get('promocion')
                
                if codigo_promocion:
                    # Prioridad 1: Código promocional ingresado
                    if codigo_promocion.aplica_a_servicio(servicio):
                        turno.promocion = codigo_promocion
                        messages.info(request, f'Se aplicó el código promocional: {codigo_promocion.codigo}')
                    else:
                        messages.warning(request, f'El código {codigo_promocion.codigo} no aplica a este servicio')
                        turno.aplicar_promocion_automatica()
                elif promocion_seleccionada:
                    # Prioridad 2: Promoción seleccionada manualmente
                    turno.promocion = promocion_seleccionada
                    messages.info(request, f'Se aplicó la promoción: {promocion_seleccionada.titulo}')
                else:
                    # Prioridad 3: Aplicar automáticamente la mejor promoción
                    mejor_promo = turno.aplicar_promocion_automatica()
                    if mejor_promo:
                        messages.success(request, f'¡Se aplicó automáticamente la promoción "{mejor_promo.titulo}"!')
                
                # Calcular precio final con descuento
                turno.precio_final = turno.calcular_precio_final()
                turno.save()
                
                # Mostrar resumen de precio
                if turno.promocion:
                    descuento = turno.calcular_descuento()
                    precio_base = turno.calcular_precio_base()
                    messages.success(
                        request, 
                        f'Turno solicitado exitosamente. '
                        f'Precio base: ${precio_base:.2f} - '
                        f'Descuento: ${descuento:.2f} - '
                        f'Total: ${turno.precio_final:.2f}. '
                        f'Esperando confirmación del profesional.'
                    )
                else:
                    messages.success(
                        request, 
                        f'Turno solicitado exitosamente. Total: ${turno.precio_final:.2f}. '
                        f'Esperando confirmación del profesional.'
                    )
                
                return redirect('turnos:ver_turno', id=turno.id)
            except (Servicio.DoesNotExist, Profesional.DoesNotExist):
                messages.error(request, 'Servicio o profesional no encontrado')
    else:
        form = SolicitarTurnoForm()
    
    return render(request, 'turnos/solicitar_turno.html', {'form': form})


@user_passes_test(es_cliente)
def obtener_servicios_por_categoria(request):
    """API para obtener servicios de una categoría"""
    categoria_id = request.GET.get('categoria_id')
    
    if not categoria_id:
        return JsonResponse({'servicios': []})
    
    servicios = Servicio.objects.filter(
        categoria_id=categoria_id,
        activo=True,
        categoria__activa=True
    ).values('id', 'nombre', 'descripcion', 'precio_base', 'duracion_estimada')
    
    return JsonResponse({'servicios': list(servicios)})


@user_passes_test(es_cliente)
def obtener_profesionales_disponibles(request):
    """API para obtener profesionales disponibles para un servicio con sus horarios"""
    servicio_id = request.GET.get('servicio_id')
    
    if not servicio_id:
        return JsonResponse({'profesionales': []})
    
    try:
        servicio = Servicio.objects.get(id=servicio_id)
        
        # Obtener todos los profesionales que ofrecen este servicio
        profesionales = Profesional.objects.filter(
            servicios=servicio,
            usuario__activo=True,
            disponible=True
        ).select_related('usuario')
        
        resultado = []
        
        # Generar disponibilidad para los próximos 14 días
        hoy = timezone.now().date()
        dias_a_mostrar = 14
        
        for profesional in profesionales:
            # Obtener horarios del profesional
            horarios = HorarioDisponibilidad.objects.filter(profesional=profesional)
            
            disponibilidad = []
            
            for i in range(dias_a_mostrar):
                fecha = hoy + timedelta(days=i)
                dia_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'][fecha.weekday()]
                
                # Buscar horario para este día
                horario_dia = horarios.filter(dia_semana=dia_semana).first()
                
                if horario_dia:
                    # Generar slots de tiempo cada hora
                    hora_actual = datetime.combine(fecha, horario_dia.hora_inicio)
                    hora_fin = datetime.combine(fecha, horario_dia.hora_fin)
                    
                    while hora_actual < hora_fin:
                        # Verificar que no haya turno en este horario
                        turno_existe = Turno.objects.filter(
                            profesional=profesional,
                            fecha=fecha,
                            hora=hora_actual.time(),
                            estado__in=['pendiente', 'confirmado', 'en_curso']
                        ).exists()
                        
                        if not turno_existe and hora_actual > timezone.now():
                            disponibilidad.append({
                                'fecha': fecha.strftime('%Y-%m-%d'),
                                'fecha_formato': fecha.strftime('%d/%m/%Y'),
                                'dia_semana': dia_semana.capitalize(),
                                'hora': hora_actual.strftime('%H:%M'),
                                'precio': float(servicio.precio_base)
                            })
                        
                        # Incrementar por la duración del servicio o 1 hora mínimo
                        incremento = max(servicio.duracion_estimada, 60)
                        hora_actual += timedelta(minutes=incremento)
            
            if disponibilidad:  # Solo agregar si tiene disponibilidad
                resultado.append({
                    'id': profesional.id,
                    'nombre': profesional.usuario.get_full_name(),
                    'calificacion': float(profesional.calificacion_promedio),
                    'experiencia': profesional.anios_experiencia,
                    'foto': profesional.usuario.foto_perfil.url if profesional.usuario.foto_perfil else None,
                    'disponibilidad': disponibilidad
                })
        
        return JsonResponse({'profesionales': resultado})
        
    except Servicio.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)


@user_passes_test(es_cliente)
def obtener_promociones_disponibles(request):
    """API para obtener promociones disponibles para un servicio"""
    servicio_id = request.GET.get('servicio_id')
    
    if not servicio_id:
        return JsonResponse({'promociones': []})
    
    try:
        from apps.promociones.models import Promocion
        servicio = Servicio.objects.get(id=servicio_id)
        now = timezone.now()
        
        # Buscar promociones vigentes
        promociones_vigentes = Promocion.objects.filter(
            activa=True,
            fecha_inicio__lte=now,
            fecha_fin__gte=now
        )
        
        # Filtrar las que aplican al servicio
        promociones_aplicables = []
        for promo in promociones_vigentes:
            if promo.aplica_a_servicio(servicio):
                descuento = promo.calcular_descuento(servicio.precio_base)
                precio_con_descuento = servicio.precio_base - descuento
                
                promociones_aplicables.append({
                    'id': promo.id,
                    'titulo': promo.titulo,
                    'descripcion': promo.descripcion,
                    'tipo_descuento': promo.get_tipo_descuento_display(),
                    'valor_descuento': float(promo.valor_descuento),
                    'descuento_calculado': float(descuento),
                    'precio_final': float(precio_con_descuento),
                    'codigo': promo.codigo if promo.codigo else None,
                    'fecha_fin': promo.fecha_fin.strftime('%d/%m/%Y %H:%M')
                })
        
        return JsonResponse({
            'promociones': promociones_aplicables,
            'precio_base': float(servicio.precio_base)
        })
        
    except Servicio.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)


@user_passes_test(es_cliente)
def validar_codigo_promocional(request):
    """API para validar un código promocional"""
    from apps.promociones.models import Promocion
    
    codigo = request.GET.get('codigo', '').strip().upper()
    servicio_id = request.GET.get('servicio_id')
    
    if not codigo or not servicio_id:
        return JsonResponse({'valido': False, 'mensaje': 'Datos incompletos'})
    
    try:
        servicio = Servicio.objects.get(id=servicio_id)
        promocion = Promocion.objects.get(codigo__iexact=codigo)
        
        if not promocion.esta_vigente():
            return JsonResponse({
                'valido': False, 
                'mensaje': 'El código promocional ha expirado o no está activo'
            })
        
        if not promocion.aplica_a_servicio(servicio):
            return JsonResponse({
                'valido': False, 
                'mensaje': 'Este código no aplica al servicio seleccionado'
            })
        
        descuento = promocion.calcular_descuento(servicio.precio_base)
        precio_final = servicio.precio_base - descuento
        
        return JsonResponse({
            'valido': True,
            'mensaje': f'¡Código válido! {promocion.titulo}',
            'promocion': {
                'id': promocion.id,
                'titulo': promocion.titulo,
                'descripcion': promocion.descripcion,
                'descuento': float(descuento),
                'precio_final': float(precio_final)
            }
        })
        
    except Promocion.DoesNotExist:
        return JsonResponse({
            'valido': False, 
            'mensaje': 'Código promocional no válido'
        })
    except Servicio.DoesNotExist:
        return JsonResponse({
            'valido': False, 
            'mensaje': 'Servicio no encontrado'
        })


# CU-24: Modificar Turno
@login_required
def modificar_turno(request, id):
    """Modificar un turno (cliente o profesional)"""
    turno = get_object_or_404(Turno, id=id)
    
    # Verificar permisos
    if not (request.user.perfil_cliente == turno.cliente or 
            request.user.perfil_profesional == turno.profesional):
        messages.error(request, 'No tienes permiso para modificar este turno')
        return redirect('turnos:historial_turnos')
    
    # Solo se puede modificar si está pendiente
    if turno.estado not in ['pendiente', 'confirmado']:
        messages.error(request, 'Este turno ya no puede ser modificado')
        return redirect('turnos:ver_turno', id=turno.id)
    
    if request.method == 'POST':
        form = ModificarTurnoForm(request.POST, instance=turno)
        if form.is_valid():
            form.save()

            messages.success(request, 'Turno modificado exitosamente')
            return redirect('turnos:ver_turno', id=turno.id)
    else:
        form = ModificarTurnoForm(instance=turno)
    
    return render(request, 'turnos/modificar_turno.html', {'form': form, 'turno': turno})


# CU-25: Cancelar Turno
@login_required
def cancelar_turno(request, id):
    """Cancelar un turno"""
    turno = get_object_or_404(Turno, id=id)
    
    # Verificar permisos
    if not (request.user.perfil_cliente == turno.cliente or 
            request.user.perfil_profesional == turno.profesional):
        messages.error(request, 'No tienes permiso para cancelar este turno')
        return redirect('turnos:historial_turnos')
    
    if turno.estado in ['completado', 'cancelado']:
        messages.error(request, 'Este turno ya no puede ser cancelado')
        return redirect('turnos:ver_turno', id=turno.id)
    
    if request.method == 'POST':
        turno.estado = 'cancelado'
        turno.save()
        
        messages.success(request, 'Turno cancelado exitosamente')
        return redirect('turnos:historial_turnos')
    
    return render(request, 'turnos/cancelar_turno.html', {'turno': turno})


# CU-26: Calificar Turno
@user_passes_test(es_cliente)
def calificar_turno(request, id):
    """Cliente califica un turno completado"""
    turno = get_object_or_404(Turno, id=id)
    
    # Verificar que sea el cliente del turno
    if request.user.perfil_cliente != turno.cliente:
        messages.error(request, 'No tienes permiso para calificar este turno')
        return redirect('turnos:historial_turnos')
    
    # Verificar que esté completado
    if turno.estado != 'completado':
        messages.error(request, 'Solo puedes calificar turnos completados')
        return redirect('turnos:ver_turno', id=turno.id)
    
    # Verificar que no esté ya calificado
    if hasattr(turno, 'calificacion'):
        messages.warning(request, 'Este turno ya fue calificado')
        return redirect('turnos:ver_turno', id=turno.id)
    
    if request.method == 'POST':
        form = CalificarTurnoForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.turno = turno
            calificacion.cliente = turno.cliente
            calificacion.save()
            
            # Actualizar calificación promedio del profesional
            profesional = turno.profesional
            calificaciones = Calificacion.objects.filter(turno__profesional=profesional)
            promedio = sum(c.puntuacion for c in calificaciones) / calificaciones.count()
            profesional.calificacion_promedio = promedio
            profesional.save()
            
            messages.success(request, 'Calificación registrada exitosamente')
            return redirect('turnos:ver_turno', id=turno.id)
    else:
        form = CalificarTurnoForm()
    
    return render(request, 'turnos/calificar_turno.html', {'form': form, 'turno': turno})


# CU-31: Ver Historial de Turnos
@login_required
def historial_turnos(request):
    """Ver historial de turnos (cliente o profesional)"""
    if request.user.is_cliente():
        # Cliente ve todos sus turnos (historial completo)
        turnos = Turno.objects.filter(
            cliente=request.user.perfil_cliente
        ).select_related('servicio', 'profesional__usuario').order_by('-fecha', '-hora')
    elif request.user.is_profesional():
        # Profesional ve todos sus turnos (historial completo)
        turnos = Turno.objects.filter(
            profesional=request.user.perfil_profesional
        ).select_related('servicio', 'cliente__usuario').order_by('-fecha', '-hora')
    else:
        # Admin ve todos los turnos
        turnos = Turno.objects.all().select_related(
            'cliente__usuario', 'profesional__usuario', 'servicio'
        ).order_by('-fecha', '-hora')
    
    return render(request, 'turnos/historial_turnos.html', {'turnos': turnos})


# CU-32: Buscar Turno
@login_required
def buscar_turno(request):
    """Buscar turnos con filtros"""
    form = BuscarTurnoForm(request.GET or None)
    turnos = None
    
    if form.is_valid():
        # Filtrar según el rol
        if request.user.is_cliente():
            turnos = Turno.objects.filter(
                cliente=request.user.perfil_cliente
            ).select_related('servicio', 'profesional__usuario')
        elif request.user.is_profesional():
            turnos = Turno.objects.filter(
                profesional=request.user.perfil_profesional
            ).select_related('servicio', 'cliente__usuario')
        else:
            # Admin ve todos
            turnos = Turno.objects.all().select_related(
                'cliente__usuario', 'profesional__usuario', 'servicio'
            )
        
        # Aplicar filtros de fecha
        if form.cleaned_data.get('fecha_desde'):
            turnos = turnos.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        
        if form.cleaned_data.get('fecha_hasta'):
            turnos = turnos.filter(fecha__lte=form.cleaned_data['fecha_hasta'])
        
        if form.cleaned_data.get('estado'):
            turnos = turnos.filter(estado=form.cleaned_data['estado'])
        
        if form.cleaned_data.get('servicio'):
            turnos = turnos.filter(servicio=form.cleaned_data['servicio'])
        
        turnos = turnos.order_by('-fecha_hora')
    
    return render(request, 'turnos/buscar_turno.html', {'form': form, 'turnos': turnos})


@login_required
def ver_turno(request, id):
    """Ver detalle de un turno"""
    turno = get_object_or_404(Turno, id=id)
    
    # Verificar permisos
    if not (request.user.is_administrador() or
            request.user.perfil_cliente == turno.cliente or
            request.user.perfil_profesional == turno.profesional):
        messages.error(request, 'No tienes permiso para ver este turno')
        return redirect('turnos:historial_turnos')
    
    return render(request, 'turnos/ver_turno.html', {'turno': turno})


@user_passes_test(es_profesional)
def confirmar_turno(request, id):
    """Profesional confirma o rechaza un turno"""
    turno = get_object_or_404(Turno, id=id)
    
    if request.user.perfil_profesional != turno.profesional:
        messages.error(request, 'No tienes permiso para confirmar este turno')
        return redirect('turnos:historial_turnos')
    
    if turno.estado != 'pendiente':
        messages.warning(request, 'Este turno ya fue procesado')
        return redirect('turnos:ver_turno', id=turno.id)
    
    if request.method == 'POST':
        form = ConfirmarTurnoForm(request.POST, instance=turno)
        if form.is_valid():
            form.save()
            messages.success(request, f'Turno {turno.estado} exitosamente')
            return redirect('turnos:ver_turno', id=turno.id)
    else:
        form = ConfirmarTurnoForm(instance=turno)
    
    return render(request, 'turnos/confirmar_turno.html', {'form': form, 'turno': turno})
