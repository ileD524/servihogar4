from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Promocion
from .forms import PromocionForm, BuscarPromocionForm


def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'


# CU-18: Registrar Promoción
@user_passes_test(es_administrador)
def registrar_promocion(request):
    """Administrador registra una nueva promoción con validaciones completas"""
    if request.method == 'POST':
        form = PromocionForm(request.POST)
        if form.is_valid():
            try:
                promocion = form.save()
                
                # Mostrar advertencia si hay solapamiento
                if hasattr(form, 'add_warning') and form.add_warning:
                    messages.warning(request, form.warning_message)
                
                messages.success(
                    request, 
                    f'Promoción "{promocion.titulo}" registrada exitosamente. '
                    f'Código: {promocion.codigo or "Sin código"}'
                )
                return redirect('promociones:ver_promocion', id=promocion.id)
            except Exception as e:
                messages.error(request, f'Error al registrar la promoción: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = PromocionForm()
    
    context = {
        'form': form,
        'titulo_pagina': 'Registrar Nueva Promoción',
        'action': 'registrar'
    }
    
    return render(request, 'promociones/registrar_promocion.html', context)


# CU-19: Modificar Promoción
@user_passes_test(es_administrador)
def modificar_promocion(request, id):
    """Administrador modifica una promoción con validaciones completas"""
    promocion = get_object_or_404(Promocion, id=id)
    
    if request.method == 'POST':
        form = PromocionForm(request.POST, instance=promocion)
        if form.is_valid():
            try:
                promocion_actualizada = form.save()
                
                # Mostrar advertencia si hay solapamiento
                if hasattr(form, 'add_warning') and form.add_warning:
                    messages.warning(request, form.warning_message)
                
                messages.success(
                    request, 
                    f'Promoción "{promocion_actualizada.titulo}" modificada exitosamente'
                )
                return redirect('promociones:ver_promocion', id=promocion.id)
            except Exception as e:
                messages.error(request, f'Error al modificar la promoción: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = PromocionForm(instance=promocion)
    
    context = {
        'form': form,
        'promocion': promocion,
        'titulo_pagina': f'Modificar Promoción: {promocion.titulo}',
        'action': 'modificar'
    }
    
    return render(request, 'promociones/modificar_promocion.html', context)


# CU-20: Eliminar Promoción
@user_passes_test(es_administrador)
def eliminar_promocion(request, id):
    """Administrador elimina (desactiva) una promoción"""
    from django.utils import timezone

    promocion = get_object_or_404(Promocion, id=id)
    
    if request.method == 'POST':
        promocion.activa = False
        promocion.fecha_eliminacion = timezone.now()
        promocion.save()

        messages.success(request, 'Promoción eliminada exitosamente')
        return redirect('promociones:buscar_promocion')
    
    return render(request, 'promociones/eliminar_promocion.html', {'promocion': promocion})


@user_passes_test(es_administrador)
def buscar_promocion(request):
    """Buscar promociones con filtros - Admin ve todas (CU-45)"""
    from django.core.paginator import Paginator
    
    form = BuscarPromocionForm(request.GET or None)
    
    # Admin ve todas las categorías (activas e inactivas)
    promociones = Promocion.objects.all()
    
    # Aplicar filtros
    if request.GET and form.is_valid():
        if form.cleaned_data.get('nombre'):
            promociones = promociones.filter(nombre__icontains=form.cleaned_data['nombre'])
        
        if form.cleaned_data.get('estado'):
            if form.cleaned_data['estado'] == 'activa':
                promociones = promociones.filter(activa=True)
            elif form.cleaned_data['estado'] == 'inactiva':
                promociones = promociones.filter(activa=False)

        if form.cleaned_data.get('fecha_inicio'):
            promociones = promociones.filter(fecha_inicio__gte=form.cleaned_data['fecha_inicio'])

        if form.cleaned_data.get('fecha_fin'):
            promociones = promociones.filter(fecha_fin__lte=form.cleaned_data['fecha_fin'])

    # Obtener parámetros de ordenamiento
    orden = request.GET.get('orden', 'id')
    direccion = request.GET.get('dir', 'asc')
    
    # Validar campos permitidos para ordenamiento
    campos_validos = ['id', 'titulo', 'activa', 'fecha_creacion', 'fecha_modificacion', 'fecha_eliminacion']
    if orden not in campos_validos:
        orden = 'id'
    
    # Aplicar ordenamiento
    if direccion == 'desc':
        orden = f'-{orden}'
    
    
    promociones = promociones.order_by(orden)
    
    # Paginación
    items_por_pagina = request.GET.get('items', 10)
    try:
        items_por_pagina = int(items_por_pagina)
    except (ValueError, TypeError):
        items_por_pagina = 10
    
    paginator = Paginator(promociones, items_por_pagina)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'promociones': page_obj,
        'page_obj': page_obj,
        'orden_actual': request.GET.get('orden', 'id'),
        'dir_actual': request.GET.get('dir', 'asc'),
        'items_por_pagina': items_por_pagina
    }
    
    return render(request, 'promociones/buscar_promocion.html', context)


@login_required
def ver_promocion(request, id):
    """Ver detalle de una promoción"""
    promocion = get_object_or_404(Promocion, id=id)
    return render(request, 'promociones/ver_promocion.html', {'promocion': promocion})


@user_passes_test(es_administrador)
def buscar_promocion(request):
    from django.core.paginator import Paginator

    form = BuscarPromocionForm(request.GET or None)

    promociones = Promocion.objects.all()

    # Aplicar filtros
    if request.GET and form.is_valid():
        if form.cleaned_data.get('nombre'):
            promociones = promociones.filter(nombre__icontains=form.cleaned_data['nombre'])
        
        if form.cleaned_data.get('activa'):
            if form.cleaned_data['activa'] == 'activo':
                promociones = promociones.filter(activa=True)
            elif form.cleaned_data['activa'] == 'inactivo':
                promociones = promociones.filter(activa=False)

        if form.cleaned_data.get('fecha_inicio'):
            promociones = promociones.filter(fecha_inicio__gte=form.cleaned_data['fecha_inicio'])

        if form.cleaned_data.get('fecha_fin'):
            promociones = promociones.filter(fecha_fin__lte=form.cleaned_data['fecha_fin'])
    
    # Obtener parámetros de ordenamiento
    orden = request.GET.get('orden', 'id')
    direccion = request.GET.get('dir', 'asc')
    
    # Validar campos permitidos para ordenamiento
    campos_validos = ['id', 'titulo', 'activa', 'fecha_creacion', 'fecha_modificacion', 'fecha_eliminacion']
    if orden not in campos_validos:
        orden = 'id'
    
    # Aplicar ordenamiento
    if direccion == 'desc':
        orden = f'-{orden}'
    
    promociones = promociones.order_by(orden)
    
    # Paginación
    items_por_pagina = request.GET.get('items', 10)
    try:
        items_por_pagina = int(items_por_pagina)
    except (ValueError, TypeError):
        items_por_pagina = 10
    
    paginator = Paginator(promociones, items_por_pagina)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'promociones': page_obj,
        'page_obj': page_obj,
        'orden_actual': request.GET.get('orden', 'id'),
        'dir_actual': request.GET.get('dir', 'asc'),
        'items_por_pagina': items_por_pagina
    }
    
    return render(request, 'promociones/buscar_promocion.html', context)


@login_required
def promociones_vigentes(request):
    """Ver promociones vigentes (para clientes)"""
    from django.utils import timezone
    now = timezone.now()
    promociones = Promocion.objects.filter(
        activa=True,
        fecha_inicio__lte=now,
        fecha_fin__gte=now
    ).order_by('-fecha_creacion')
    
    return render(request, 'promociones/promociones_vigentes.html', {'promociones': promociones})


# ==================== VISTAS AJAX PARA MODALES ====================

@user_passes_test(es_administrador)
def ver_promocion_ajax(request, id):
    """Vista AJAX para ver detalle de promoción en modal"""
    from django.http import JsonResponse
    promocion = get_object_or_404(Promocion, id=id)
    
    context = {
        'promocion': promocion,
        'is_ajax': True
    }
    
    return render(request, 'promociones/ver_promocion_ajax.html', context)


@user_passes_test(es_administrador)
def modificar_promocion_ajax(request, id):
    """Vista AJAX para modificar promoción en modal"""
    from django.http import JsonResponse
    promocion = get_object_or_404(Promocion, id=id)
    
    if request.method == 'POST':
        form = PromocionForm(request.POST, instance=promocion)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Promoción actualizada correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = PromocionForm(instance=promocion)
        context = {
            'form': form,
            'promocion': promocion,
            'is_ajax': True
        }
        return render(request, 'promociones/modificar_promocion_ajax.html', context)


@user_passes_test(es_administrador)
def registrar_promocion_ajax(request):
    """Vista AJAX para registrar promoción desde modal"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        form = PromocionForm(request.POST)
        if form.is_valid():
            try:
                promocion = form.save()
                
                message = f'Promoción "{promocion.titulo}" registrada exitosamente.'
                if promocion.codigo:
                    message += f' Código: {promocion.codigo}'
                
                # Añadir advertencia de solapamiento si existe
                if hasattr(form, 'add_warning') and form.add_warning:
                    message += f' ADVERTENCIA: {form.warning_message}'
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'promocion_id': promocion.id
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [f'Error al registrar: {str(e)}']}
                })
        else:
            # Retornar errores del formulario
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(e) for e in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })
    
    return JsonResponse({'success': False, 'errors': {'__all__': ['Método no permitido']}})


@user_passes_test(es_administrador)
def modificar_promocion_ajax(request, id):
    """Vista AJAX para modificar promoción desde modal"""
    from django.http import JsonResponse
    
    promocion = get_object_or_404(Promocion, id=id)
    
    if request.method == 'POST':
        form = PromocionForm(request.POST, instance=promocion)
        if form.is_valid():
            try:
                promocion_actualizada = form.save()
                
                message = f'Promoción "{promocion_actualizada.titulo}" modificada exitosamente.'
                
                # Añadir advertencia de solapamiento si existe
                if hasattr(form, 'add_warning') and form.add_warning:
                    message += f' ADVERTENCIA: {form.warning_message}'
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'promocion_id': promocion_actualizada.id
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [f'Error al modificar: {str(e)}']}
                })
        else:
            # Retornar errores del formulario
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(e) for e in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })
    else:
        # GET - Retornar formulario HTML
        form = PromocionForm(instance=promocion)
        context = {
            'form': form,
            'promocion': promocion,
            'is_ajax': True
        }
        return render(request, 'promociones/modificar_promocion_ajax.html', context)
    
@user_passes_test(es_administrador)
def obtener_promocion_ajax(request, id):
    """Vista AJAX para obtener datos de una promoción"""
    from django.http import JsonResponse
    
    promocion = get_object_or_404(Promocion, id=id)
    
    data = {
        'id': promocion.id,
        'titulo': promocion.titulo,
        'descripcion': promocion.descripcion,
        'codigo': promocion.codigo,
        'tipo_descuento': promocion.tipo_descuento,
        'valor_descuento': str(promocion.valor_descuento),
        'categoria': promocion.categoria_id,
        'servicios': list(promocion.servicios.values_list('id', flat=True)),
        'fecha_inicio': promocion.fecha_inicio.isoformat(),
        'fecha_fin': promocion.fecha_fin.isoformat(),
        'activa': promocion.activa
    }
    
    return JsonResponse(data)


@user_passes_test(es_administrador)
def eliminar_promocion_ajax(request, id):
    """Vista AJAX para eliminar promoción"""
    from django.http import JsonResponse
    from django.utils import timezone
    
    if request.method == 'POST':
        promocion = get_object_or_404(Promocion, id=id)
        
        try:
            promocion.activa = False
            promocion.fecha_eliminacion = timezone.now()
            promocion.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Promoción eliminada correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar promoción: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@user_passes_test(es_administrador)
def activar_promocion_ajax(request, id):
    """Vista AJAX para activar promoción"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        promocion = get_object_or_404(Promocion, id=id)
        
        try:
            promocion.activa = True
            promocion.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Promoción activada correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al activar promoción: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})
