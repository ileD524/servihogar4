from django.db import models

class PoliticaCancelacion(models.Model):
    """Políticas de cancelación"""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    horas_anticipacion = models.IntegerField(help_text="Horas de anticipación requeridas")
    penalizacion_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de penalización")
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Política de Cancelación'
        verbose_name_plural = 'Políticas de Cancelación'
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return self.titulo


class PoliticaReembolso(models.Model):
    """Políticas de reembolso"""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    dias_reembolso = models.IntegerField(help_text="Días para procesar el reembolso")
    porcentaje_reembolso = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje a reembolsar")
    condiciones = models.TextField()
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Política de Reembolso'
        verbose_name_plural = 'Políticas de Reembolso'
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return self.titulo
