from django.contrib import admin
from .models import Categoria, Servicio

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activa', 'fecha_creacion']
    list_filter = ['activa']
    search_fields = ['nombre']

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'descripcion', 'duracion_estimada', 'precio_base', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre', 'categoria', 'profesional__usuario__username', 'activo']
