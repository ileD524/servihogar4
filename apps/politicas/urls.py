from django.urls import path
from . import views

app_name = 'politicas'

urlpatterns = [
    # === POLÍTICAS DE REEMBOLSO ===
    # CU-19: Registrar Política de Reembolso
    path('reembolso/registrar/', views.registrar_politica_reembolso, name='registrar_politica_reembolso'),
    
    # CU-22: Modificar Política de Reembolso
    path('reembolso/modificar/<int:id>/', views.modificar_politica_reembolso, name='modificar_politica_reembolso'),
    
    # CU-23: Eliminar Política de Reembolso
    path('reembolso/eliminar/<int:id>/', views.eliminar_politica_reembolso, name='eliminar_politica_reembolso'),
    
    # === POLÍTICAS DE CANCELACIÓN ===
    path('cancelacion/registrar/', views.registrar_politica_cancelacion, name='registrar_politica_cancelacion'),
    
    # CU-25: Modificar Política de Cancelación
    path('cancelacion/modificar/<int:id>/', views.modificar_politica_cancelacion, name='modificar_politica_cancelacion'),
    
    # CU-26: Eliminar Política de Cancelación
    path('cancelacion/eliminar/<int:id>/', views.eliminar_politica_cancelacion, name='eliminar_politica_cancelacion'),
    
    # CU-46: Buscar Política
    path('buscar/', views.buscar_politica, name='buscar_politica'),
    
    # Vistas adicionales
    path('cancelacion/ver/<int:id>/', views.ver_politica_cancelacion, name='ver_politica_cancelacion'),
    path('reembolso/ver/<int:id>/', views.ver_politica_reembolso, name='ver_politica_reembolso'),
    path('cancelacion/listar/', views.listar_politicas_cancelacion, name='listar_politicas_cancelacion'),
    path('reembolso/listar/', views.listar_politicas_reembolso, name='listar_politicas_reembolso'),
]
