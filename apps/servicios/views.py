from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import Servicio, Categoria
from .forms import BuscarServicioForm, BuscarCategoriaForm, ServicioForm, CategoriaForm

# En este archivo se va a encontrar gran parte de la logica de la aplicacion
# Aqui se van a definir las vistas que van a manejar las solicitudes HTTP (POST, GET, ...)

def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'


# ==================== GESTIÓN DE CATEGORÍAS ====================

# CU-36: Registrar Categoría
@user_passes_test(es_administrador)
def registrar_categoria(request):
    """Administrador registra nueva categoría de servicios (CU-36)"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            # Verificar que el nombre no exista
            nombre = form.cleaned_data['nombre']
            if Categoria.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, 'Ya existe una categoría con ese nombre')
                return render(request, 'servicios/registrar_categoria.html', {'form': form})
            
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" registrada exitosamente')
            return redirect('servicios:buscar_categoria')
    else:
        form = CategoriaForm()
    
    return render(request, 'servicios/registrar_categoria.html', {'form': form})


# CU-37: Modificar Categoría
@user_passes_test(es_administrador)
def modificar_categoria(request, id):
    """Administrador modifica categoría existente (CU-37)"""
    from django.utils import timezone
    categoria = get_object_or_404(Categoria, id=id)
    estado_anterior = categoria.activa  # Guardar el estado anterior ANTES del formulario
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            # Verificar que el nuevo nombre no coincida con otra categoría
            nombre = form.cleaned_data['nombre']
            if Categoria.objects.filter(nombre__iexact=nombre).exclude(id=categoria.id).exists():
                messages.error(request, 'Ya existe otra categoría con ese nombre')
                return render(request, 'servicios/modificar_categoria.html', {'form': form, 'categoria': categoria})
            
            # Guardar sin commit para manejar fecha_eliminacion
            categoria_actualizada = form.save(commit=False)
            
            # Manejar fecha de eliminación según el cambio de estado
            if not estado_anterior and categoria_actualizada.activa:
                # Si se reactivó la categoría (estaba inactiva y ahora activa)
                categoria_actualizada.fecha_eliminacion = None
                # Reactivar todos sus servicios y limpiar sus fechas de eliminación
                servicios_reactivados = Servicio.objects.filter(categoria=categoria_actualizada).update(
                    activo=True,
                    fecha_eliminacion=None
                )
                messages.success(request, 
                    f'Categoría "{categoria_actualizada.nombre}" reactivada. '
                    f'{servicios_reactivados} servicio(s) reactivado(s).')
            elif estado_anterior and not categoria_actualizada.activa:
                # Si se desactivó la categoría (estaba activa y ahora inactiva)
                categoria_actualizada.fecha_eliminacion = timezone.now()
                # Desactivar todos sus servicios y establecer sus fechas de eliminación
                servicios_desactivados = Servicio.objects.filter(categoria=categoria_actualizada).update(
                    activo=False,
                    fecha_eliminacion=timezone.now()
                )
                messages.success(request, 
                    f'Categoría "{categoria_actualizada.nombre}" desactivada. '
                    f'{servicios_desactivados} servicio(s) desactivado(s).')
            else:
                messages.success(request, f'Categoría "{categoria_actualizada.nombre}" modificada exitosamente')
            
            categoria_actualizada.save()
            return redirect('servicios:buscar_categoria')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'servicios/modificar_categoria.html', {'form': form, 'categoria': categoria})


# Vista auxiliar para toggle de estado de categoría (sin formulario completo)
@user_passes_test(es_administrador)
def toggle_categoria(request, id):
    """Activa o desactiva una categoría con cascada a servicios"""
    from django.utils import timezone
    categoria = get_object_or_404(Categoria, id=id)
    estado_anterior = categoria.activa
    
    # Toggle del estado
    categoria.activa = not categoria.activa
    
    # Manejar fecha de eliminación
    if categoria.activa:
        categoria.fecha_eliminacion = None
    else:
        categoria.fecha_eliminacion = timezone.now()
    
    categoria.save()
    
    if categoria.activa and not estado_anterior:
        # Se reactivó: reactivar todos sus servicios y limpiar fecha_eliminacion
        servicios_afectados = Servicio.objects.filter(categoria=categoria).update(
            activo=True,
            fecha_eliminacion=None
        )
        messages.success(request, 
            f'Categoría "{categoria.nombre}" activada. '
            f'{servicios_afectados} servicio(s) reactivado(s).')
    elif not categoria.activa and estado_anterior:
        # Se desactivó: desactivar todos sus servicios y establecer fecha_eliminacion
        servicios_afectados = Servicio.objects.filter(categoria=categoria).update(
            activo=False,
            fecha_eliminacion=timezone.now()
        )
        messages.success(request, 
            f'Categoría "{categoria.nombre}" desactivada. '
            f'{servicios_afectados} servicio(s) desactivado(s).')
    
    return redirect('servicios:buscar_categoria')


# CU-38: Eliminar Categoría
@user_passes_test(es_administrador)
def eliminar_categoria(request, id):
    """Administrador elimina categoría (lógica) y sus servicios asociados (CU-38)"""
    from django.utils import timezone
    categoria = get_object_or_404(Categoria, id=id)
    
    # Obtener TODOS los servicios de esta categoría (activos e inactivos)
    servicios_categoria = Servicio.objects.filter(categoria=categoria)
    profesionales_afectados = servicios_categoria.values('profesional').distinct().count()
    
    if request.method == 'POST':
        # Marcar categoría como inactiva y establecer fecha_eliminacion
        categoria.activa = False
        categoria.fecha_eliminacion = timezone.now()
        categoria.save()
        
        # Marcar TODOS los servicios de esta categoría como inactivos y establecer fecha_eliminacion
        servicios_afectados = servicios_categoria.update(
            activo=False,
            fecha_eliminacion=timezone.now()
        )
        
        messages.success(request, 
            f'Categoría "{categoria.nombre}" eliminada. '
            f'{servicios_afectados} servicio(s) desactivado(s).')
        return redirect('servicios:buscar_categoria')
    
    context = {
        'categoria': categoria,
        'servicios_count': servicios_categoria.count(),
        'profesionales_count': profesionales_afectados
    }
    return render(request, 'servicios/eliminar_categoria.html', context)


# CU-40: Buscar Categoría
@user_passes_test(es_administrador)
def buscar_categoria(request):
    """Buscar categorías con filtros - Admin ve todas (CU-40)"""
    from django.core.paginator import Paginator
    
    form = BuscarCategoriaForm(request.GET or None)
    
    # Admin ve todas las categorías (activas e inactivas)
    categorias = Categoria.objects.all()
    
    # Aplicar filtros
    if request.GET and form.is_valid():
        if form.cleaned_data.get('nombre'):
            categorias = categorias.filter(nombre__icontains=form.cleaned_data['nombre'])
        
        if form.cleaned_data.get('estado'):
            if form.cleaned_data['estado'] == 'activa':
                categorias = categorias.filter(activa=True)
            elif form.cleaned_data['estado'] == 'inactiva':
                categorias = categorias.filter(activa=False)
    
    # Obtener parámetros de ordenamiento
    orden = request.GET.get('orden', 'id')
    direccion = request.GET.get('dir', 'asc')
    
    # Validar campos permitidos para ordenamiento
    campos_validos = ['id', 'nombre', 'activa', 'fecha_creacion', 'fecha_modificacion', 'fecha_eliminacion', 'servicios']
    if orden not in campos_validos:
        orden = 'id'
    
    # Aplicar ordenamiento
    if direccion == 'desc':
        orden = f'-{orden}'
    
    # Para ordenar por número de servicios, usar annotate
    if 'servicios' in orden:
        from django.db.models import Count
        categorias = categorias.annotate(num_servicios=Count('servicios'))
        orden = orden.replace('servicios', 'num_servicios')
    
    categorias = categorias.order_by(orden)
    
    # Paginación
    items_por_pagina = request.GET.get('items', 10)
    try:
        items_por_pagina = int(items_por_pagina)
    except (ValueError, TypeError):
        items_por_pagina = 10
    
    paginator = Paginator(categorias, items_por_pagina)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'categorias': page_obj,
        'page_obj': page_obj,
        'orden_actual': request.GET.get('orden', 'id'),
        'dir_actual': request.GET.get('dir', 'asc'),
        'items_por_pagina': items_por_pagina
    }
    
    return render(request, 'servicios/buscar_categoria.html', context)


# ==================== GESTIÓN DE SERVICIOS ====================

# CU-13: Registrar Servicio
@user_passes_test(es_administrador)
def registrar_servicio(request):
    """Administrador registra nuevo servicio (CU-13)"""
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            # Verificar que el nombre del servicio no exista previamente
            nombre = form.cleaned_data['nombre']
            if Servicio.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, 'Ya existe un servicio con ese nombre')
                return render(request, 'servicios/registrar_servicio.html', {'form': form})
            
            servicio = form.save()
            messages.success(request, f'Servicio "{servicio.nombre}" registrado exitosamente')
            return redirect('servicios:buscar_servicio')
    else:
        form = ServicioForm()
    
    return render(request, 'servicios/registrar_servicio.html', {'form': form})


# CU-14: Eliminar Servicio
@user_passes_test(es_administrador)
def eliminar_servicio(request, id):
    """Administrador elimina servicio (lógica) verificando turnos activos (CU-14)"""
    from django.utils import timezone
    servicio = get_object_or_404(Servicio, id=id)
    
    # Verificar si hay turnos activos asociados
    from apps.turnos.models import Turno
    turnos_activos = Turno.objects.filter(
        servicio=servicio,
        estado__in=['pendiente', 'confirmado']
    )
    
    if turnos_activos.exists():
        messages.error(request, 
            f'No se puede eliminar el servicio "{servicio.nombre}" porque tiene '
            f'{turnos_activos.count()} turno(s) activo(s) asociado(s).')
        return redirect('servicios:buscar_servicio')
    
    if request.method == 'POST':
        # Marcar servicio como inactivo y establecer fecha de eliminación
        servicio.activo = False
        servicio.fecha_eliminacion = timezone.now()
        servicio.save()
        
        messages.success(request, f'Servicio "{servicio.nombre}" eliminado exitosamente')
        return redirect('servicios:buscar_servicio')
    
    return render(request, 'servicios/eliminar_servicio.html', {'servicio': servicio})


# Activar Servicio
@user_passes_test(es_administrador)
def activar_servicio(request, id):
    """Administrador reactiva un servicio eliminado"""
    servicio = get_object_or_404(Servicio, id=id)
    
    # Verificar que la categoría esté activa
    if not servicio.categoria.activa:
        messages.error(request, 
            f'No se puede activar el servicio "{servicio.nombre}" porque '
            f'su categoría "{servicio.categoria.nombre}" está inactiva.')
        return redirect('servicios:buscar_servicio')
    
    # Reactivar servicio y limpiar fecha de eliminación
    servicio.activo = True
    servicio.fecha_eliminacion = None
    servicio.save()
    
    messages.success(request, f'Servicio "{servicio.nombre}" reactivado exitosamente')
    return redirect('servicios:buscar_servicio')


# CU-15: Modificar Servicio
@user_passes_test(es_administrador)
def modificar_servicio(request, id):
    """Administrador modifica servicio existente (CU-15)"""
    from django.utils import timezone
    servicio = get_object_or_404(Servicio, id=id)
    estado_anterior = servicio.activo  # Guardar el estado anterior
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            # Verificar que el nuevo nombre no coincida con otro servicio
            nombre = form.cleaned_data['nombre']
            if Servicio.objects.filter(nombre__iexact=nombre).exclude(id=servicio.id).exists():
                messages.error(request, 'Ya existe otro servicio con ese nombre')
                return render(request, 'servicios/modificar_servicio.html', {'form': form, 'servicio': servicio})
            
            # Guardar sin commit para manejar fecha_eliminacion
            servicio_actualizado = form.save(commit=False)
            
            # Manejar fecha de eliminación según el cambio de estado
            if not estado_anterior and servicio_actualizado.activo:
                # Si se reactivó el servicio (estaba inactivo y ahora activo)
                # Verificar que la categoría esté activa
                if not servicio_actualizado.categoria.activa:
                    messages.error(request, 
                        f'No se puede activar el servicio porque su categoría '
                        f'"{servicio_actualizado.categoria.nombre}" está inactiva.')
                    return render(request, 'servicios/modificar_servicio.html', {'form': form, 'servicio': servicio})
                
                servicio_actualizado.fecha_eliminacion = None
                messages.success(request, f'Servicio "{servicio_actualizado.nombre}" reactivado exitosamente')
            elif estado_anterior and not servicio_actualizado.activo:
                # Si se desactivó el servicio (estaba activo y ahora inactivo)
                servicio_actualizado.fecha_eliminacion = timezone.now()
                messages.success(request, f'Servicio "{servicio_actualizado.nombre}" desactivado exitosamente')
            else:
                messages.success(request, f'Servicio "{servicio_actualizado.nombre}" modificado exitosamente')
            
            servicio_actualizado.save()
            return redirect('servicios:buscar_servicio')
    else:
        form = ServicioForm(instance=servicio)
    
    return render(request, 'servicios/modificar_servicio.html', {'form': form, 'servicio': servicio})


# CU-39: Buscar Servicio
@user_passes_test(es_administrador)
def buscar_servicio(request):
    """Buscar servicios con filtros - Admin ve todos (CU-39)"""
    from django.core.paginator import Paginator
    
    form = BuscarServicioForm(request.GET or None)
    
    # Admin ve todos los servicios (activos e inactivos)
    servicios = Servicio.objects.all().select_related('categoria', 'profesional__usuario')
    
    # Aplicar filtros
    if request.GET and form.is_valid():
        if form.cleaned_data.get('nombre'):
            servicios = servicios.filter(nombre__icontains=form.cleaned_data['nombre'])
        
        if form.cleaned_data.get('categoria'):
            servicios = servicios.filter(categoria=form.cleaned_data['categoria'])
        
        if form.cleaned_data.get('estado'):
            if form.cleaned_data['estado'] == 'activo':
                servicios = servicios.filter(activo=True)
            elif form.cleaned_data['estado'] == 'inactivo':
                servicios = servicios.filter(activo=False)
    
    # Obtener parámetros de ordenamiento
    orden = request.GET.get('orden', 'id')
    direccion = request.GET.get('dir', 'asc')
    
    # Validar campos permitidos para ordenamiento
    campos_validos = ['id', 'nombre', 'categoria__nombre', 'precio_base', 'duracion_estimada', 'activo', 'fecha_creacion', 'fecha_modificacion', 'fecha_eliminacion']
    if orden not in campos_validos:
        orden = 'id'
    
    # Aplicar ordenamiento
    if direccion == 'desc':
        orden = f'-{orden}'
    
    servicios = servicios.order_by(orden)
    
    # Paginación
    items_por_pagina = request.GET.get('items', 10)
    try:
        items_por_pagina = int(items_por_pagina)
    except (ValueError, TypeError):
        items_por_pagina = 10
    
    paginator = Paginator(servicios, items_por_pagina)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'servicios': page_obj,
        'page_obj': page_obj,
        'orden_actual': request.GET.get('orden', 'id'),
        'dir_actual': request.GET.get('dir', 'asc'),
        'items_por_pagina': items_por_pagina
    }
    
    return render(request, 'servicios/buscar_servicio.html', context)


@login_required
def ver_servicio(request, id):
    """Ver detalle de un servicio"""
    servicio = get_object_or_404(Servicio, id=id)
    return render(request, 'servicios/ver_servicio.html', {'servicio': servicio})


@login_required
def ver_categoria(request, id):
    """Ver detalle de una categoría y sus servicios"""
    categoria = get_object_or_404(Categoria, id=id)
    # Admin ve todos los servicios (activos e inactivos) de esta categoría
    servicios = Servicio.objects.filter(categoria=categoria).select_related('profesional__usuario')
    return render(request, 'servicios/ver_categoria.html', {'categoria': categoria, 'servicios': servicios})


# ==================== VISTAS AJAX PARA MODALES - SERVICIOS ====================

@user_passes_test(es_administrador)
def ver_servicio_ajax(request, id):
    """Vista AJAX para ver detalle de servicio en modal"""
    from django.http import JsonResponse
    servicio = get_object_or_404(Servicio, id=id)
    
    context = {
        'servicio': servicio,
        'is_ajax': True
    }
    
    return render(request, 'servicios/ver_servicio_ajax.html', context)


@user_passes_test(es_administrador)
def modificar_servicio_ajax(request, id):
    """Vista AJAX para modificar servicio en modal"""
    from django.http import JsonResponse
    servicio = get_object_or_404(Servicio, id=id)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Servicio actualizado correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = ServicioForm(instance=servicio)
        context = {
            'form': form,
            'servicio': servicio,
            'is_ajax': True
        }
        return render(request, 'servicios/modificar_servicio_ajax.html', context)


@user_passes_test(es_administrador)
def eliminar_servicio_ajax(request, id):
    """Vista AJAX para eliminar servicio"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        servicio = get_object_or_404(Servicio, id=id)
        
        try:
            from django.utils import timezone
            servicio.activo = False
            servicio.fecha_eliminacion = timezone.now()
            servicio.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Servicio eliminado correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar servicio: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@user_passes_test(es_administrador)
def activar_servicio_ajax(request, id):
    """Vista AJAX para activar servicio"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        servicio = get_object_or_404(Servicio, id=id)
        
        try:
            servicio.activo = True
            servicio.fecha_eliminacion = None
            servicio.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Servicio activado correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al activar servicio: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


# ==================== VISTAS AJAX PARA MODALES - CATEGORÍAS ====================

@user_passes_test(es_administrador)
def ver_categoria_ajax(request, id):
    """Vista AJAX para ver detalle de categoría en modal"""
    from django.http import JsonResponse
    categoria = get_object_or_404(Categoria, id=id)
    servicios = Servicio.objects.filter(categoria=categoria)
    
    context = {
        'categoria': categoria,
        'servicios': servicios,
        'is_ajax': True
    }
    
    return render(request, 'servicios/ver_categoria_ajax.html', context)


@user_passes_test(es_administrador)
def modificar_categoria_ajax(request, id):
    """Vista AJAX para modificar categoría en modal"""
    from django.http import JsonResponse
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Categoría actualizada correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = CategoriaForm(instance=categoria)
        context = {
            'form': form,
            'categoria': categoria,
            'is_ajax': True
        }
        return render(request, 'servicios/modificar_categoria_ajax.html', context)


@user_passes_test(es_administrador)
def eliminar_categoria_ajax(request, id):
    """Vista AJAX para eliminar categoría"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        categoria = get_object_or_404(Categoria, id=id)
        
        # Verificar si tiene servicios asociados
        if categoria.servicios.exists():
            return JsonResponse({
                'success': False,
                'message': 'No se puede eliminar una categoría que tiene servicios asociados'
            })
        
        try:
            from django.utils import timezone
            categoria.activa = False
            categoria.fecha_eliminacion = timezone.now()
            categoria.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Categoría eliminada correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar categoría: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@user_passes_test(es_administrador)
def activar_categoria_ajax(request, id):
    """Vista AJAX para activar categoría"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        categoria = get_object_or_404(Categoria, id=id)
        
        try:
            categoria.activa = True
            categoria.fecha_eliminacion = None
            categoria.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Categoría activada correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al activar categoría: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
