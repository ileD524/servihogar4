from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cliente, Profesional

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'rol', 'activo']
    list_filter = ['rol', 'activo', 'fecha_registro']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('rol', 'telefono', 'direccion', 'latitud', 'longitud', 'foto_perfil', 'activo', 'google_id')
        }),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'get_email']
    search_fields = ['usuario__username', 'usuario__email']
    
    def get_email(self, obj):
        return obj.usuario.email
    get_email.short_description = 'Email'

@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'get_email', 'calificacion_promedio', 'disponible']
    list_filter = ['disponible']
    search_fields = ['usuario__username', 'usuario__email']
    
    def get_email(self, obj):
        return obj.usuario.email
    get_email.short_description = 'Email'
