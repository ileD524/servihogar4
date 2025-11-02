from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Menú principal de reportes
    path('', views.menu_reportes, name='menu_reportes'),
    
    # CU-34: Generar Reporte de Preferencias y Comportamientos de Cliente
    path('generar/preferencias-cliente/', views.generar_reporte_preferencias_cliente, name='generar_reporte_preferencias_cliente'),
    
    # Otros reportes
    path('generar/servicios-populares/', views.generar_reporte_servicios_populares, name='generar_reporte_servicios_populares'),
    path('generar/ingresos/', views.generar_reporte_ingresos, name='generar_reporte_ingresos'),
    path('generar/profesionales/', views.generar_reporte_profesionales, name='generar_reporte_profesionales'),
    
    # Ver reportes
    path('ver/<int:id>/', views.ver_reporte, name='ver_reporte'),
    path('listar/', views.listar_reportes, name='listar_reportes'),
]
