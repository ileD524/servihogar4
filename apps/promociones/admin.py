from django.contrib import admin
from .models import Promocion

@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_descuento', 'valor_descuento', 'fecha_inicio', 'fecha_fin', 'activa']
    list_filter = ['tipo_descuento', 'activa', 'fecha_inicio']
    search_fields = ['titulo', 'codigo']
    filter_horizontal = ['servicios']
