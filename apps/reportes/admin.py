from django.contrib import admin
from .models import Reporte

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'fecha_generacion', 'generado_por']
    list_filter = ['tipo', 'fecha_generacion']
    search_fields = ['titulo', 'descripcion']
    readonly_fields = ['fecha_generacion']
