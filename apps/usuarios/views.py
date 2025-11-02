from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import Usuario, Cliente, Profesional
from .forms import (RegistroUsuarioForm, ModificarUsuarioForm, LoginForm, 
                    RegistrarUsuarioAdminForm, BuscarUsuarioForm)
import requests
from django.conf import settings


def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return user.is_authenticated and user.rol == 'administrador'


def es_cliente(user):
    """Verifica si el usuario es cliente"""
    return user.is_authenticated and user.rol == 'cliente'


def es_profesional(user):
    """Verifica si el usuario es profesional"""
    return user.is_authenticated and user.rol == 'profesional'


# CU-04: Registrar Usuario
def registrar_usuario(request):
    """Registro de nuevo usuario"""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Si es profesional, procesar horarios
            if user.rol == 'profesional':
                import json
                from apps.usuarios.models import HorarioDisponibilidad
                
                horarios_json = request.POST.get('horarios_json', '[]')
                try:
                    horarios_data = json.loads(horarios_json)
                    profesional = user.perfil_profesional
                    
                    for horario in horarios_data:
                        HorarioDisponibilidad.objects.create(
                            profesional=profesional,
                            dia_semana=horario['dia'],
                            hora_inicio=horario['hora_inicio'],
                            hora_fin=horario['hora_fin']
                        )
                except (json.JSONDecodeError, KeyError) as e:
                    messages.warning(request, 'Error al guardar horarios. Podrás configurarlos desde tu perfil.')
            
            messages.success(request, 'Usuario registrado exitosamente. Ya puedes iniciar sesión.')
            return redirect('usuarios:login')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'usuarios/registrar_usuario.html', {'form': form})


# CU-07: Iniciar Sesión
def iniciar_sesion(request):
    """Inicio de sesión convencional"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido {user.get_full_name()}')
                # Redirigir según el rol
                if user.rol == 'administrador':
                    return redirect('usuarios:dashboard_admin')
                elif user.rol == 'profesional':
                    return redirect('usuarios:dashboard_profesional')
                else:  # cliente
                    return redirect('usuarios:dashboard_cliente')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    return render(request, 'usuarios/login.html', {'form': form})


# Login con Google OAuth (API)
def google_login(request):
    """Redirige a Google para autenticación OAuth"""
    google_auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={settings.GOOGLE_OAUTH_CLIENT_ID}&redirect_uri=http://localhost:8000/usuarios/google/callback/&response_type=code&scope=openid%20email%20profile"
    return redirect(google_auth_url)


def google_callback(request):
    """Callback de Google OAuth"""
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Error en la autenticación con Google')
        return redirect('usuarios:login')
    
    # Intercambiar código por token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
        'redirect_uri': 'http://localhost:8000/usuarios/google/callback/',
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        # Obtener información del usuario
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()
        
        # Buscar o crear usuario
        google_id = user_info.get('id')
        email = user_info.get('email')
        
        user, created = Usuario.objects.get_or_create(
            google_id=google_id,
            defaults={
                'username': email.split('@')[0],
                'email': email,
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'rol': 'cliente'
            }
        )
        
        if created:
            Cliente.objects.create(usuario=user)
        
        login(request, user)
        messages.success(request, f'Bienvenido {user.get_full_name()}')
        # Redirigir según el rol
        if user.rol == 'administrador':
            return redirect('usuarios:dashboard_admin')
        elif user.rol == 'profesional':
            return redirect('usuarios:dashboard_profesional')
        else:  # cliente
            return redirect('usuarios:dashboard_cliente')
        
    except Exception as e:
        messages.error(request, f'Error al autenticar con Google: {str(e)}')
        return redirect('usuarios:login')


# CU-08: Cerrar Sesión
@login_required
def cerrar_sesion(request):
    """Cierre de sesión"""
    user = request.user
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('usuarios:login')


# CU-03: Modificar Perfil (usuario modifica su propio perfil)
@login_required
def modificar_perfil(request):
    """Usuario modifica su propio perfil (CU-03)"""
    usuario = request.user
    
    # El administrador NO puede modificar su perfil desde aquí
    if usuario.is_administrador():
        messages.error(request, 'Los administradores no pueden modificar su perfil desde esta sección')
        return redirect('usuarios:dashboard_admin')
    
    if request.method == 'POST':
        form = ModificarUsuarioForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil modificado exitosamente')
            return redirect('usuarios:perfil', id=usuario.id)
    else:
        form = ModificarUsuarioForm(instance=usuario)
    
    return render(request, 'usuarios/modificar_usuario.html', {'form': form, 'usuario': usuario})


# CU-02: Eliminar Perfil (usuario da de baja su propia cuenta)
@login_required
def eliminar_perfil(request):
    """Usuario elimina (da de baja) su propio perfil (CU-02) - Baja lógica"""
    usuario = request.user
    
    # El administrador NO puede eliminar su propia cuenta desde aquí
    if usuario.is_administrador():
        messages.error(request, 'Los administradores no pueden eliminar su cuenta desde esta sección')
        return redirect('usuarios:dashboard_admin')
    
    if request.method == 'POST':
        # Verificar que no tenga turnos activos o solicitudes pendientes
        if usuario.is_cliente():
            from apps.turnos.models import Turno
            turnos_activos = Turno.objects.filter(
                cliente=usuario.perfil_cliente,
                estado__in=['pendiente', 'confirmado']
            ).exists()
            
            if turnos_activos:
                messages.error(request, 'No puedes eliminar tu cuenta mientras tengas turnos activos o pendientes')
                return redirect('usuarios:perfil', id=usuario.id)
        
        elif usuario.is_profesional():
            from apps.turnos.models import Turno
            turnos_activos = Turno.objects.filter(
                profesional=usuario.perfil_profesional,
                estado__in=['pendiente', 'confirmado']
            ).exists()
            
            if turnos_activos:
                messages.error(request, 'No puedes eliminar tu cuenta mientras tengas turnos activos o pendientes')
                return redirect('usuarios:perfil', id=usuario.id)
        
        # Marcar como inactivo (baja lógica)
        username = usuario.username
        usuario.activo = False
        usuario.save()
        
        # Cerrar sesión
        logout(request)
        messages.success(request, f'Tu cuenta ha sido eliminada exitosamente. Esperamos verte pronto.')
        return redirect('home')
    
    return render(request, 'usuarios/eliminar_usuario.html', {'usuario': usuario})


# Modificar Usuario (solo para ADMINISTRADOR)
@user_passes_test(es_administrador)
def modificar_usuario(request, id):
    """Administrador modifica usuario (cliente o profesional)"""
    usuario = get_object_or_404(Usuario, id=id)
    
    # El admin no puede modificar otros administradores (pero sí a sí mismo)
    if usuario.is_administrador() and usuario.id != request.user.id:
        messages.error(request, 'No puedes modificar otros administradores')
        return redirect('usuarios:buscar_usuario')
    
    if request.method == 'POST':
        form = ModificarUsuarioForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            # Guardar datos básicos
            usuario_actualizado = form.save(commit=False)
            
            # Manejar fecha de eliminación según el estado
            if usuario_actualizado.activo and usuario.fecha_eliminacion:
                # Si se reactivó el usuario, limpiar fecha de eliminación
                usuario_actualizado.fecha_eliminacion = None
            elif not usuario_actualizado.activo and not usuario.fecha_eliminacion:
                # Si se desactivó el usuario, registrar fecha de eliminación
                from django.utils import timezone
                usuario_actualizado.fecha_eliminacion = timezone.now()
            
            usuario_actualizado.save()
            
            # Si es profesional, actualizar servicios y horarios
            if usuario_actualizado.rol == 'profesional':
                import json
                from apps.usuarios.models import HorarioDisponibilidad
                from apps.servicios.models import Servicio
                
                # Obtener el perfil profesional
                profesional = usuario_actualizado.perfil_profesional
                
                # Actualizar años de experiencia
                anios_exp = form.cleaned_data.get('anios_experiencia', 0)
                profesional.anios_experiencia = anios_exp
                profesional.save()
                
                # Actualizar servicios
                servicios_seleccionados = form.cleaned_data.get('servicios', [])
                
                # Primero, desasignar todos los servicios actuales de este profesional
                Servicio.objects.filter(profesional=profesional).update(profesional=None)
                
                # Luego, asignar los nuevos servicios seleccionados
                for servicio in servicios_seleccionados:
                    servicio.profesional = profesional
                    servicio.save()
                
                # Actualizar horarios
                horarios_json = request.POST.get('horarios_json', '[]')
                try:
                    horarios_data = json.loads(horarios_json)
                    profesional = usuario_actualizado.perfil_profesional
                    
                    # Eliminar horarios existentes
                    HorarioDisponibilidad.objects.filter(profesional=profesional).delete()
                    
                    # Crear nuevos horarios
                    for horario in horarios_data:
                        HorarioDisponibilidad.objects.create(
                            profesional=profesional,
                            dia_semana=horario['dia'],
                            hora_inicio=horario['hora_inicio'],
                            hora_fin=horario['hora_fin']
                        )
                except (json.JSONDecodeError, KeyError) as e:
                    messages.warning(request, 'Error al actualizar horarios.')
            
            messages.success(request, 'Usuario modificado exitosamente')
            return redirect('usuarios:perfil', id=usuario_actualizado.id)
    else:
        form = ModificarUsuarioForm(instance=usuario)
    
    # Obtener horarios actuales si es profesional
    horarios_actuales = []
    if usuario.rol == 'profesional':
        try:
            import json
            horarios_obj = usuario.perfil_profesional.horarios.all()
            horarios_actuales = [
                {
                    'dia_semana': h.dia_semana,
                    'hora_inicio': h.hora_inicio.strftime('%H:%M'),
                    'hora_fin': h.hora_fin.strftime('%H:%M')
                }
                for h in horarios_obj
            ]
            horarios_actuales = json.dumps(horarios_actuales)
        except:
            horarios_actuales = '[]'
    else:
        horarios_actuales = '[]'
    
    return render(request, 'usuarios/modificar_usuario.html', {
        'form': form, 
        'usuario': usuario,
        'horarios_actuales': horarios_actuales
    })


# CU-06: Eliminar Usuario (solo para ADMINISTRADOR) - Baja lógica
@user_passes_test(es_administrador)
# CU-06: Eliminar Usuario (solo para ADMINISTRADOR) - Baja lógica
@user_passes_test(es_administrador)
def eliminar_usuario(request, id):
    """Administrador elimina usuario (cliente o profesional) - Baja lógica"""
    usuario = get_object_or_404(Usuario, id=id)
    
    # El admin no puede eliminar otros administradores
    if usuario.is_administrador():
        messages.error(request, 'No puedes eliminar otros administradores')
        return redirect('usuarios:buscar_usuario')
    
    if request.method == 'POST':
        from django.utils import timezone
        username = usuario.username
        usuario.activo = False
        usuario.fecha_eliminacion = timezone.now()
        usuario.save()
        messages.success(request, f'Usuario {username} eliminado exitosamente')
        return redirect('usuarios:buscar_usuario')
    
    return render(request, 'usuarios/eliminar_usuario.html', {'usuario': usuario})


# CU-06B: Activar Usuario (solo para ADMINISTRADOR)
@user_passes_test(es_administrador)
def activar_usuario(request, id):
    """Administrador reactiva usuario (cliente o profesional)"""
    usuario = get_object_or_404(Usuario, id=id)
    
    # El admin no puede activar otros administradores
    if usuario.is_administrador():
        messages.error(request, 'No puedes activar otros administradores')
        return redirect('usuarios:buscar_usuario')
    
    username = usuario.username
    usuario.activo = True
    usuario.fecha_eliminacion = None
    usuario.save()
    messages.success(request, f'Usuario {username} activado exitosamente')
    return redirect('usuarios:buscar_usuario')


# CU-04: Registrar Usuario (ADMINISTRADOR registra cliente o profesional)
@user_passes_test(es_administrador)
def registrar_usuario_admin(request):
    """Administrador registra nuevo usuario (cliente o profesional) - CU-04"""
    if request.method == 'POST':
        form = RegistrarUsuarioAdminForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Si es profesional, procesar horarios
            if user.rol == 'profesional':
                import json
                from apps.usuarios.models import HorarioDisponibilidad
                from apps.servicios.models import Servicio
                
                horarios_json = request.POST.get('horarios_json', '[]')
                try:
                    horarios_data = json.loads(horarios_json)
                    profesional = user.perfil_profesional
                    
                    for horario in horarios_data:
                        HorarioDisponibilidad.objects.create(
                            profesional=profesional,
                            dia_semana=horario['dia'],
                            hora_inicio=horario['hora_inicio'],
                            hora_fin=horario['hora_fin']
                        )
                except (json.JSONDecodeError, KeyError) as e:
                    messages.warning(request, 'Error al guardar horarios. Podrás configurarlos desde el perfil del usuario.')
                
                # Procesar servicios seleccionados
                servicios_ids = request.POST.getlist('servicios')
                if servicios_ids:
                    for servicio_id in servicios_ids:
                        servicio = Servicio.objects.get(id=servicio_id)
                        servicio.profesional = profesional
                        servicio.save()
            
            messages.success(request, f'Usuario {user.username} registrado exitosamente como {user.get_rol_display()}')
            return redirect('usuarios:buscar_usuario')
    else:
        form = RegistrarUsuarioAdminForm()
    
    # Obtener servicios disponibles para profesionales
    from apps.servicios.models import Servicio
    servicios_disponibles = Servicio.objects.filter(activo=True, categoria__activa=True, profesional__isnull=True)
    
    return render(request, 'usuarios/registrar_usuario_admin.html', {
        'form': form,
        'servicios_disponibles': servicios_disponibles
    })


# CU-42: Buscar Usuario
@user_passes_test(es_administrador)
def buscar_usuario(request):
    """Buscar usuarios con filtros (CU-42)"""
    form = BuscarUsuarioForm(request.GET or None)
    
    # Siempre mostrar todos los usuarios por defecto
    usuarios = Usuario.objects.all()
    
    if request.GET and form.is_valid():
        # Filtro por nombre
        if form.cleaned_data.get('nombre'):
            usuarios = usuarios.filter(first_name__icontains=form.cleaned_data['nombre'])
        
        # Filtro por apellido
        if form.cleaned_data.get('apellido'):
            usuarios = usuarios.filter(last_name__icontains=form.cleaned_data['apellido'])
        
        # Filtro por rol
        if form.cleaned_data.get('rol'):
            usuarios = usuarios.filter(rol=form.cleaned_data['rol'])
        
        # Filtro por estado
        if form.cleaned_data.get('estado'):
            if form.cleaned_data['estado'] == 'activo':
                usuarios = usuarios.filter(activo=True)
            elif form.cleaned_data['estado'] == 'inactivo':
                usuarios = usuarios.filter(activo=False)
    
    usuarios = usuarios.order_by('-fecha_registro')
    
    return render(request, 'usuarios/buscar_usuario.html', {'form': form, 'usuarios': usuarios})


@login_required
def perfil_usuario(request, id):
    """Ver perfil de usuario"""
    usuario = get_object_or_404(Usuario, id=id)
    context = {'usuario': usuario}
    
    if usuario.is_cliente():
        context['perfil'] = usuario.perfil_cliente
    elif usuario.is_profesional():
        from apps.turnos.models import Calificacion
        from apps.servicios.models import Servicio
        from django.db.models import Avg
        
        perfil = usuario.perfil_profesional
        context['perfil'] = perfil
        
        # Calcular calificación promedio desde turnos calificados
        calificacion_promedio = Calificacion.objects.filter(
            turno__profesional=perfil
        ).aggregate(promedio=Avg('puntuacion'))['promedio']
        
        # Si tiene calificaciones, actualizar el promedio; si no, es 0
        if calificacion_promedio is not None:
            perfil.calificacion_promedio = round(calificacion_promedio, 2)
        else:
            perfil.calificacion_promedio = 0.0
        perfil.save()
        
        context['calificacion_promedio'] = perfil.calificacion_promedio
        
        # Obtener servicios que ofrece el profesional
        servicios_ofrecidos = Servicio.objects.filter(profesional=perfil, activo=True)
        context['servicios_ofrecidos'] = servicios_ofrecidos
    
    return render(request, 'usuarios/perfil.html', context)


# Vista principal (home)
def home(request):
    """Página principal - redirige a dashboard según rol si está logueado, sino al login"""
    if request.user.is_authenticated:
        if request.user.rol == 'administrador':
            return redirect('usuarios:dashboard_admin')
        elif request.user.rol == 'profesional':
            return redirect('usuarios:dashboard_profesional')
        else:  # cliente
            return redirect('usuarios:dashboard_cliente')
    # Si no está autenticado, redirigir al login
    return redirect('usuarios:login')


# ========== DASHBOARDS ==========

@login_required
@user_passes_test(es_cliente)
def dashboard_cliente(request):
    """Dashboard para clientes"""
    from apps.turnos.models import Turno
    from apps.servicios.models import Servicio
    
    # Obtener el perfil de cliente del usuario
    try:
        cliente = request.user.perfil_cliente
    except Cliente.DoesNotExist:
        # Si no existe el perfil de cliente, crearlo
        cliente = Cliente.objects.create(usuario=request.user)
    
    turnos_pendientes = Turno.objects.filter(
        cliente=cliente, 
        estado='pendiente',
        servicio__activo=True,
        profesional__usuario__activo=True
    ).select_related('servicio', 'profesional').order_by('fecha', 'hora')[:5]
    
    turnos_confirmados = Turno.objects.filter(
        cliente=cliente, 
        estado='confirmado',
        servicio__activo=True,
        profesional__usuario__activo=True
    ).select_related('servicio', 'profesional').order_by('fecha', 'hora')[:5]
    
    historial_turnos = Turno.objects.filter(
        cliente=cliente, 
        estado__in=['completado', 'cancelado']
    ).select_related('servicio', 'profesional').order_by('-fecha', '-hora')[:5]
    
    # Solo servicios activos, con profesionales activos y categorías activas
    servicios_destacados = Servicio.objects.filter(
        activo=True,
        profesional__usuario__activo=True,
        categoria__activa=True
    ).select_related('categoria', 'profesional__usuario').order_by('-id')[:6]
    
    context = {
        'turnos_pendientes': turnos_pendientes,
        'turnos_confirmados': turnos_confirmados,
        'historial_turnos': historial_turnos,
        'servicios_destacados': servicios_destacados,
        'total_turnos': Turno.objects.filter(cliente=cliente).count(),
    }
    return render(request, 'usuarios/dashboard_cliente.html', context)


@login_required
@user_passes_test(es_profesional)
def dashboard_profesional(request):
    """Dashboard para profesionales"""
    from apps.turnos.models import Turno
    from apps.servicios.models import Servicio
    
    profesional = request.user.perfil_profesional
    
    # Turnos pendientes de confirmación (solo de clientes activos con servicios activos)
    turnos_pendientes = Turno.objects.filter(
        profesional=profesional, 
        estado='pendiente',
        cliente__usuario__activo=True,
        servicio__activo=True
    ).select_related('cliente', 'servicio').order_by('fecha', 'hora')[:5]
    
    # Turnos confirmados próximos (solo de clientes activos con servicios activos)
    turnos_confirmados = Turno.objects.filter(
        profesional=profesional, 
        estado='confirmado',
        cliente__usuario__activo=True,
        servicio__activo=True
    ).select_related('cliente', 'servicio').order_by('fecha', 'hora')[:5]
    
    # Historial reciente (incluye todos porque son históricos)
    historial_turnos = Turno.objects.filter(
        profesional=profesional, 
        estado__in=['completado', 'cancelado']
    ).select_related('cliente', 'servicio').order_by('-fecha', '-hora')[:5]
    
    # Servicios del profesional (solo los activos)
    mis_servicios = Servicio.objects.filter(
        profesional=profesional, 
        activo=True,
        categoria__activa=True
    ).select_related('categoria')
    
    # Estadísticas (solo turnos con clientes activos para estadísticas actuales)
    total_turnos = Turno.objects.filter(
        profesional=profesional,
        cliente__usuario__activo=True
    ).count()
    turnos_completados = Turno.objects.filter(
        profesional=profesional, 
        estado='completado',
        cliente__usuario__activo=True
    ).count()
    
    context = {
        'turnos_pendientes': turnos_pendientes,
        'turnos_confirmados': turnos_confirmados,
        'historial_turnos': historial_turnos,
        'mis_servicios': mis_servicios,
        'total_turnos': total_turnos,
        'turnos_completados': turnos_completados,
    }
    return render(request, 'usuarios/dashboard_profesional.html', context)


@login_required
@user_passes_test(es_administrador)
def dashboard_admin(request):
    """Dashboard para administradores"""
    from apps.turnos.models import Turno
    from apps.servicios.models import Servicio, Categoria
    from apps.promociones.models import Promocion
    from apps.politicas.models import PoliticaCancelacion
    from django.db.models import Count
    from datetime import date
    
    # Estadísticas generales
    total_usuarios = Usuario.objects.filter(activo=True).count()
    total_clientes = Usuario.objects.filter(rol='cliente', activo=True).count()
    total_profesionales = Usuario.objects.filter(rol='profesional', activo=True).count()
    total_servicios = Servicio.objects.filter(activo=True).count()
    total_categorias = Categoria.objects.filter(activa=True).count()
    total_turnos = Turno.objects.count()
    turnos_pendientes = Turno.objects.filter(estado='pendiente').count()
    turnos_hoy = Turno.objects.filter(fecha=date.today()).count()
    
    # Promociones activas
    promociones_activas = Promocion.objects.filter(
        activa=True,
        fecha_inicio__lte=date.today(),
        fecha_fin__gte=date.today()
    ).count()
    
    # Usuarios recientes
    usuarios_recientes = Usuario.objects.filter(activo=True).order_by('-fecha_registro')[:5]
    
    # Turnos recientes (mostrar todos para el admin, incluyendo de usuarios inactivos)
    turnos_recientes = Turno.objects.select_related(
        'cliente__usuario', 'profesional__usuario', 'servicio'
    ).order_by('-fecha_solicitud')[:5]
    
    # Servicios más solicitados (solo servicios activos)
    servicios_populares = Servicio.objects.filter(
        activo=True,
        profesional__usuario__activo=True
    ).annotate(
        num_turnos=Count('turnos')
    ).order_by('-num_turnos')[:5]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_clientes': total_clientes,
        'total_profesionales': total_profesionales,
        'total_servicios': total_servicios,
        'total_categorias': total_categorias,
        'total_turnos': total_turnos,
        'turnos_pendientes': turnos_pendientes,
        'turnos_hoy': turnos_hoy,
        'promociones_activas': promociones_activas,
        'usuarios_recientes': usuarios_recientes,
        'turnos_recientes': turnos_recientes,
        'servicios_populares': servicios_populares,
    }
    return render(request, 'usuarios/dashboard_admin.html', context)
