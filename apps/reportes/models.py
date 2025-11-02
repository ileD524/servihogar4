from django.db import models
from apps.usuarios.models import Usuario

class Reporte(models.Model):
    """Reportes generados del sistema"""
    TIPOS = (
        ('preferencias_cliente', 'Preferencias y Comportamientos de Cliente'),
        ('servicios_populares', 'Servicios Más Populares'),
        ('ingresos', 'Ingresos'),
        ('profesionales', 'Desempeño de Profesionales'),
    )
    
    tipo = models.CharField(max_length=50, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    generado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='reportes')
    datos_json = models.JSONField(help_text="Datos del reporte en formato JSON")
    
    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-fecha_generacion']
        
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_generacion}"
