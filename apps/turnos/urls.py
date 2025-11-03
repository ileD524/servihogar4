from django.urls import path
from . import views

app_name = 'turnos'

urlpatterns = [
    # CU-23: Solicitar Turno
    path('solicitar/', views.solicitar_turno, name='solicitar_turno'),
    
    # APIs para solicitar turno
    path('api/servicios-por-categoria/', views.obtener_servicios_por_categoria, name='servicios_por_categoria'),
    path('api/profesionales-disponibles/', views.obtener_profesionales_disponibles, name='profesionales_disponibles'),
    
    # CU-24: Modificar Turno
    path('modificar/<int:id>/', views.modificar_turno, name='modificar_turno'),
    
    # CU-25: Cancelar Turno
    path('cancelar/<int:id>/', views.cancelar_turno, name='cancelar_turno'),
    
    # CU-26: Calificar Turno
    path('calificar/<int:id>/', views.calificar_turno, name='calificar_turno'),
    
    # CU-31: Ver Historial de Turnos
    path('historial/', views.historial_turnos, name='historial_turnos'),
    
    # CU-32: Buscar Turno
    path('buscar/', views.buscar_turno, name='buscar_turno'),
    
    # Vistas adicionales
    path('ver/<int:id>/', views.ver_turno, name='ver_turno'),
    path('confirmar/<int:id>/', views.confirmar_turno, name='confirmar_turno'),
]
