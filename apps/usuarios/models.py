from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """Modelo extendido de Usuario con roles"""
    ROLES = (
        ('cliente', 'Cliente'),
        ('profesional', 'Profesional'),
        ('administrador', 'Administrador'),
    )
    
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='usuarios/', blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"
    
    def is_cliente(self):
        return self.rol == 'cliente'
    
    def is_profesional(self):
        return self.rol == 'profesional'
    
    def is_administrador(self):
        return self.rol == 'administrador'


class Cliente(models.Model):
    """Información adicional para clientes"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_cliente')
    preferencias = models.TextField(blank=True, null=True)
    historial_busquedas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        
    def __str__(self):
        return f"Cliente: {self.usuario.get_full_name()}"


class Profesional(models.Model):
    """Información adicional para profesionales"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_profesional')
    especialidades = models.TextField(help_text="Especialidades del profesional")
    anios_experiencia = models.IntegerField(default=0)
    certificaciones = models.TextField(blank=True, null=True)
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    disponible = models.BooleanField(default=True)
    radio_cobertura_km = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    
    class Meta:
        verbose_name = 'Profesional'
        verbose_name_plural = 'Profesionales'
        
    def __str__(self):
        return f"Profesional: {self.usuario.get_full_name()}"


class HorarioDisponibilidad(models.Model):
    """Horarios de disponibilidad del profesional"""
    DIAS_SEMANA = (
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    )
    
    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.CharField(max_length=10, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    class Meta:
        verbose_name = 'Horario de Disponibilidad'
        verbose_name_plural = 'Horarios de Disponibilidad'
        unique_together = ('profesional', 'dia_semana')
        
    def __str__(self):
        return f"{self.profesional.usuario.get_full_name()} - {self.get_dia_semana_display()}: {self.hora_inicio} - {self.hora_fin}"

