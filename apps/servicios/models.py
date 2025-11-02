from django.db import models
from apps.usuarios.models import Profesional

class Categoria(models.Model):
    """Categorías de servicios"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
        
    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    """Servicios ofrecidos por profesionales"""
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='servicios')
    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name='servicios', null=True, blank=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_estimada = models.IntegerField(help_text="Duración en minutos")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        if self.profesional:
            return f"{self.nombre} - {self.profesional.usuario.get_full_name()}"
        return self.nombre
