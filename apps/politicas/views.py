from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import PoliticaCancelacion, PoliticaReembolso
from .forms import PoliticaCancelacionForm, PoliticaReembolsoForm, BuscarPoliticaForm


def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'


# === POLÍTICAS DE REEMBOLSO ===

# CU-19: Registrar Política de Reembolso
@user_passes_test(es_administrador)
def registrar_politica_reembolso(request):
    """Administrador registra política de reembolso"""
    if request.method == 'POST':
        form = PoliticaReembolsoForm(request.POST)
        if form.is_valid():
            politica = form.save()

            messages.success(request, 'Política de reembolso registrada exitosamente')
            return redirect('politicas:ver_politica_reembolso', id=politica.id)
    else:
        form = PoliticaReembolsoForm()
    
    return render(request, 'politicas/registrar_politica_reembolso.html', {'form': form})


# CU-22: Modificar Política de Reembolso
@user_passes_test(es_administrador)
def modificar_politica_reembolso(request, id):
    """Administrador modifica política de reembolso"""
    politica = get_object_or_404(PoliticaReembolso, id=id)
    
    if request.method == 'POST':
        form = PoliticaReembolsoForm(request.POST, instance=politica)
        if form.is_valid():
            form.save()

            messages.success(request, 'Política de reembolso modificada exitosamente')
            return redirect('politicas:ver_politica_reembolso', id=politica.id)
    else:
        form = PoliticaReembolsoForm(instance=politica)
    
    return render(request, 'politicas/modificar_politica_reembolso.html', {'form': form, 'politica': politica})


# CU-23: Eliminar Política de Reembolso
@user_passes_test(es_administrador)
def eliminar_politica_reembolso(request, id):
    """Administrador elimina (desactiva) política de reembolso"""
    politica = get_object_or_404(PoliticaReembolso, id=id)
    
    if request.method == 'POST':
        politica.activa = False
        politica.save()

        messages.success(request, 'Política de reembolso eliminada exitosamente')
        return redirect('politicas:listar_politicas_reembolso')
    
    return render(request, 'politicas/eliminar_politica_reembolso.html', {'politica': politica})


# === POLÍTICAS DE CANCELACIÓN ===

# Registrar Política de Cancelación
@user_passes_test(es_administrador)
def registrar_politica_cancelacion(request):
    """Administrador registra política de cancelación"""
    if request.method == 'POST':
        form = PoliticaCancelacionForm(request.POST)
        if form.is_valid():
            politica = form.save()

            messages.success(request, 'Política de cancelación registrada exitosamente')
            return redirect('politicas:ver_politica_cancelacion', id=politica.id)
    else:
        form = PoliticaCancelacionForm()
    
    return render(request, 'politicas/registrar_politica_cancelacion.html', {'form': form})


# CU-25: Modificar Política de Cancelación
@user_passes_test(es_administrador)
def modificar_politica_cancelacion(request, id):
    """Administrador modifica política de cancelación"""
    politica = get_object_or_404(PoliticaCancelacion, id=id)
    
    if request.method == 'POST':
        form = PoliticaCancelacionForm(request.POST, instance=politica)
        if form.is_valid():
            form.save()

            messages.success(request, 'Política de cancelación modificada exitosamente')
            return redirect('politicas:ver_politica_cancelacion', id=politica.id)
    else:
        form = PoliticaCancelacionForm(instance=politica)
    
    return render(request, 'politicas/modificar_politica_cancelacion.html', {'form': form, 'politica': politica})


# CU-26: Eliminar Política de Cancelación
@user_passes_test(es_administrador)
def eliminar_politica_cancelacion(request, id):
    """Administrador elimina (desactiva) política de cancelación"""
    politica = get_object_or_404(PoliticaCancelacion, id=id)
    
    if request.method == 'POST':
        politica.activa = False
        politica.save()

        messages.success(request, 'Política de cancelación eliminada exitosamente')
        return redirect('politicas:listar_politicas_cancelacion')
    
    return render(request, 'politicas/eliminar_politica_cancelacion.html', {'politica': politica})


# CU-46: Buscar Política
@login_required
def buscar_politica(request):
    """Buscar políticas"""
    form = BuscarPoliticaForm(request.GET or None)
    politicas_cancelacion = []
    politicas_reembolso = []
    
    if form.is_valid():
        tipo = form.cleaned_data.get('tipo')
        activa = form.cleaned_data.get('activa')
        
        if tipo == '' or tipo == 'cancelacion':
            politicas_cancelacion = PoliticaCancelacion.objects.all()
            if activa:
                politicas_cancelacion = politicas_cancelacion.filter(activa=True)
        
        if tipo == '' or tipo == 'reembolso':
            politicas_reembolso = PoliticaReembolso.objects.all()
            if activa:
                politicas_reembolso = politicas_reembolso.filter(activa=True)
    
    return render(request, 'politicas/buscar_politica.html', {
        'form': form,
        'politicas_cancelacion': politicas_cancelacion,
        'politicas_reembolso': politicas_reembolso
    })


@login_required
def ver_politica_cancelacion(request, id):
    """Ver detalle de política de cancelación"""
    politica = get_object_or_404(PoliticaCancelacion, id=id)
    return render(request, 'politicas/ver_politica_cancelacion.html', {'politica': politica})


@login_required
def ver_politica_reembolso(request, id):
    """Ver detalle de política de reembolso"""
    politica = get_object_or_404(PoliticaReembolso, id=id)
    return render(request, 'politicas/ver_politica_reembolso.html', {'politica': politica})


@user_passes_test(es_administrador)
def listar_politicas_cancelacion(request):
    """Listar políticas de cancelación (admin)"""
    politicas = PoliticaCancelacion.objects.all().order_by('-fecha_creacion')
    return render(request, 'politicas/listar_politicas_cancelacion.html', {'politicas': politicas})


@user_passes_test(es_administrador)
def listar_politicas_reembolso(request):
    """Listar políticas de reembolso (admin)"""
    politicas = PoliticaReembolso.objects.all().order_by('-fecha_creacion')
    return render(request, 'politicas/listar_politicas_reembolso.html', {'politicas': politicas})
