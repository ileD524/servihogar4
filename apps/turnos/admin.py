from django.contrib import admin
from .models import Turno, Pago, Calificacion

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'profesional', 'servicio', 'fecha', 'hora', 'estado']
    list_filter = ['estado', 'fecha', 'hora']
    search_fields = ['cliente__usuario__username', 'profesional__usuario__username', 'servicio__nombre']
    date_hierarchy = 'fecha'

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'turno', 'metodo', 'monto', 'estado', 'fecha_pago']
    list_filter = ['metodo', 'estado']
    search_fields = ['turno__id', 'mercadopago_id']

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('turno', 'cliente', 'puntuacion', 'fecha')
    list_filter = ('puntuacion', 'fecha')
    search_fields = ('cliente__username', 'turno__id', 'comentario')
    readonly_fields = ('fecha',)