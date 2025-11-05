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
    """Administrador registra una nueva promoción"""
    if request.method == 'POST':
        form = PromocionForm(request.POST)
        if form.is_valid():
            promocion = form.save()

            messages.success(request, 'Promoción registrada exitosamente')
            return redirect('promociones:ver_promocion', id=promocion.id)
    else:
        form = PromocionForm()
    
    return render(request, 'promociones/registrar_promocion.html', {'form': form})


# CU-19: Modificar Promoción
@user_passes_test(es_administrador)
def modificar_promocion(request, id):
    """Administrador modifica una promoción"""
    promocion = get_object_or_404(Promocion, id=id)
    
    if request.method == 'POST':
        form = PromocionForm(request.POST, instance=promocion)
        if form.is_valid():
            form.save()

            messages.success(request, 'Promoción modificada exitosamente')
            return redirect('promociones:ver_promocion', id=promocion.id)
    else:
        form = PromocionForm(instance=promocion)
    
    return render(request, 'promociones/modificar_promocion.html', {'form': form, 'promocion': promocion})


# CU-20: Eliminar Promoción
@user_passes_test(es_administrador)
def eliminar_promocion(request, id):
    """Administrador elimina (desactiva) una promoción"""
    promocion = get_object_or_404(Promocion, id=id)
    
    if request.method == 'POST':
        promocion.activa = False
        promocion.save()

        messages.success(request, 'Promoción eliminada exitosamente')
        return redirect('promociones:listar_promociones')
    
    return render(request, 'promociones/eliminar_promocion.html', {'promocion': promocion})


# CU-45: Buscar Promoción
@login_required
def buscar_promocion(request):
    """Buscar promociones"""
    form = BuscarPromocionForm(request.GET or None)
    promociones = Promocion.objects.all()
    
    if form.is_valid():
        if form.cleaned_data.get('titulo'):
            promociones = promociones.filter(titulo__icontains=form.cleaned_data['titulo'])
        
        if form.cleaned_data.get('codigo'):
            promociones = promociones.filter(codigo__icontains=form.cleaned_data['codigo'])
        
        if form.cleaned_data.get('activa'):
            promociones = promociones.filter(activa=True)
    
    promociones = promociones.order_by('-fecha_creacion')
    return render(request, 'promociones/buscar_promocion.html', {'form': form, 'promociones': promociones})


@login_required
def ver_promocion(request, id):
    """Ver detalle de una promoción"""
    promocion = get_object_or_404(Promocion, id=id)
    return render(request, 'promociones/ver_promocion.html', {'promocion': promocion})


@user_passes_test(es_administrador)
def listar_promociones(request):
    """Listar todas las promociones (admin)"""
    promociones = Promocion.objects.all().order_by('-fecha_creacion')
    return render(request, 'promociones/listar_promociones.html', {'promociones': promociones})


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
def eliminar_promocion_ajax(request, id):
    """Vista AJAX para eliminar promoción"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        promocion = get_object_or_404(Promocion, id=id)
        
        try:
            promocion.activa = False
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
