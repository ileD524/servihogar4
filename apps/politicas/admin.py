from django.contrib import admin
from .models import PoliticaCancelacion, PoliticaReembolso

@admin.register(PoliticaCancelacion)
class PoliticaCancelacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'horas_anticipacion', 'penalizacion_porcentaje', 'activa']
    list_filter = ['activa']
    search_fields = ['titulo']

@admin.register(PoliticaReembolso)
class PoliticaReembolsoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'dias_reembolso', 'porcentaje_reembolso', 'activa']
    list_filter = ['activa']
    search_fields = ['titulo']
