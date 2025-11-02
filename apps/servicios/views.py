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
    categoria = get_object_or_404(Categoria, id=id)
    estado_anterior = categoria.activa
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            # Verificar que el nuevo nombre no coincida con otra categoría
            nombre = form.cleaned_data['nombre']
            if Categoria.objects.filter(nombre__iexact=nombre).exclude(id=categoria.id).exists():
                messages.error(request, 'Ya existe otra categoría con ese nombre')
                return render(request, 'servicios/modificar_categoria.html', {'form': form, 'categoria': categoria})
            
            categoria_actualizada = form.save()
            
            # Si se reactivó la categoría, reactivar todos sus servicios
            if not estado_anterior and categoria_actualizada.activa:
                servicios_reactivados = Servicio.objects.filter(categoria=categoria_actualizada).update(activo=True)
                messages.success(request, 
                    f'Categoría "{categoria_actualizada.nombre}" reactivada. '
                    f'{servicios_reactivados} servicio(s) reactivado(s).')
            else:
                messages.success(request, f'Categoría "{categoria_actualizada.nombre}" modificada exitosamente')
            
            return redirect('servicios:buscar_categoria')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'servicios/modificar_categoria.html', {'form': form, 'categoria': categoria})


# Vista auxiliar para toggle de estado de categoría (sin formulario completo)
@user_passes_test(es_administrador)
def toggle_categoria(request, id):
    """Activa o desactiva una categoría con cascada a servicios"""
    categoria = get_object_or_404(Categoria, id=id)
    estado_anterior = categoria.activa
    
    # Toggle del estado
    categoria.activa = not categoria.activa
    categoria.save()
    
    if categoria.activa and not estado_anterior:
        # Se reactivó: reactivar todos sus servicios
        servicios_afectados = Servicio.objects.filter(categoria=categoria).update(activo=True)
        messages.success(request, 
            f'Categoría "{categoria.nombre}" activada. '
            f'{servicios_afectados} servicio(s) reactivado(s).')
    elif not categoria.activa and estado_anterior:
        # Se desactivó: desactivar todos sus servicios
        servicios_afectados = Servicio.objects.filter(categoria=categoria).update(activo=False)
        messages.success(request, 
            f'Categoría "{categoria.nombre}" desactivada. '
            f'{servicios_afectados} servicio(s) desactivado(s).')
    
    return redirect('servicios:buscar_categoria')


# CU-38: Eliminar Categoría
@user_passes_test(es_administrador)
def eliminar_categoria(request, id):
    """Administrador elimina categoría (lógica) y sus servicios asociados (CU-38)"""
    categoria = get_object_or_404(Categoria, id=id)
    
    # Obtener TODOS los servicios de esta categoría (activos e inactivos)
    servicios_categoria = Servicio.objects.filter(categoria=categoria)
    profesionales_afectados = servicios_categoria.values('profesional').distinct().count()
    
    if request.method == 'POST':
        # Marcar categoría como inactiva
        categoria.activa = False
        categoria.save()
        
        # Marcar TODOS los servicios de esta categoría como inactivos
        servicios_afectados = servicios_categoria.update(activo=False)
        
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
        # Marcar servicio como inactivo
        servicio.activo = False
        servicio.save()
        
        messages.success(request, f'Servicio "{servicio.nombre}" eliminado exitosamente')
        return redirect('servicios:buscar_servicio')
    
    return render(request, 'servicios/eliminar_servicio.html', {'servicio': servicio})


# CU-15: Modificar Servicio
@user_passes_test(es_administrador)
def modificar_servicio(request, id):
    """Administrador modifica servicio existente (CU-15)"""
    servicio = get_object_or_404(Servicio, id=id)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            # Verificar que el nuevo nombre no coincida con otro servicio
            nombre = form.cleaned_data['nombre']
            if Servicio.objects.filter(nombre__iexact=nombre).exclude(id=servicio.id).exists():
                messages.error(request, 'Ya existe otro servicio con ese nombre')
                return render(request, 'servicios/modificar_servicio.html', {'form': form, 'servicio': servicio})
            
            form.save()
            messages.success(request, f'Servicio "{servicio.nombre}" modificado exitosamente')
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


@user_passes_test(es_administrador)
def registrar_servicio(request):
    """Administrador registra nuevo servicio"""
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save()
            messages.success(request, 'Servicio registrado exitosamente')
            return redirect('servicios:buscar_servicio')
    else:
        form = ServicioForm()
    
    return render(request, 'servicios/registrar_servicio.html', {'form': form})


@user_passes_test(es_administrador)
def modificar_servicio(request, id):
    """Administrador modifica servicio"""
    servicio = get_object_or_404(Servicio, id=id)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()

            messages.success(request, 'Servicio modificado exitosamente')
            return redirect('servicios:buscar_servicio')
    else:
        form = ServicioForm(instance=servicio)
    
    return render(request, 'servicios/modificar_servicio.html', {'form': form, 'servicio': servicio})


@user_passes_test(es_administrador)
def eliminar_servicio(request, id):
    """Administrador elimina (desactiva) servicio"""
    servicio = get_object_or_404(Servicio, id=id)
    
    if request.method == 'POST':
        servicio.activo = False
        servicio.save()

        messages.success(request, 'Servicio eliminado exitosamente')
        return redirect('servicios:buscar_servicio')
    
    return render(request, 'servicios/eliminar_servicio.html', {'servicio': servicio})


@user_passes_test(es_administrador)
def registrar_categoria(request):
    """Administrador registra nueva categoría"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()

            messages.success(request, 'Categoría registrada exitosamente')
            return redirect('servicios:ver_categoria', id=categoria.id)
    else:
        form = CategoriaForm()
    
    return render(request, 'servicios/registrar_categoria.html', {'form': form})


@user_passes_test(es_administrador)
def modificar_categoria(request, id):
    """Administrador modifica categoría"""
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()

            messages.success(request, 'Categoría modificada exitosamente')
            return redirect('servicios:ver_categoria', id=categoria.id)
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'servicios/modificar_categoria.html', {'form': form, 'categoria': categoria})


@user_passes_test(es_administrador)
def eliminar_categoria(request, id):
    """Administrador elimina (desactiva) categoría"""
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        categoria.activa = False
        categoria.save()

        messages.success(request, 'Categoría eliminada exitosamente')
        return redirect('servicios:buscar_categoria')
    
    return render(request, 'servicios/eliminar_categoria.html', {'categoria': categoria})
