from django.db import models
from apps.servicios.models import Categoria, Servicio

class Promocion(models.Model):
    """Promociones del sistema"""
    TIPOS = (
        ('porcentaje', 'Porcentaje'),
        ('monto_fijo', 'Monto Fijo'),
    )
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo_descuento = models.CharField(max_length=20, choices=TIPOS)
    valor_descuento = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='promociones', blank=True, null=True)
    servicios = models.ManyToManyField(Servicio, related_name='promociones', blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)
    codigo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return self.titulo
    
    def esta_vigente(self):
        """Verifica si la promoción está vigente"""
        from django.utils import timezone
        now = timezone.now()
        return self.activa and self.fecha_inicio <= now <= self.fecha_fin
    
    def calcular_descuento(self, monto_base):
        """Calcula el descuento aplicado a un monto base"""
        if not self.esta_vigente():
            return 0
        
        if self.tipo_descuento == 'porcentaje':
            descuento = monto_base * (self.valor_descuento / 100)
        else:  # monto_fijo
            descuento = self.valor_descuento
        
        # El descuento no puede ser mayor al monto base
        return min(descuento, monto_base)
    
    def aplica_a_servicio(self, servicio):
        """Verifica si la promoción aplica a un servicio específico"""
        if not self.esta_vigente():
            return False
        
        # Si tiene servicios específicos, verificar si está incluido
        if self.servicios.exists():
            return self.servicios.filter(id=servicio.id).exists()
        
        # Si tiene categoría, verificar si el servicio pertenece a esa categoría
        if self.categoria:
            return servicio.categoria_id == self.categoria_id
        
        # Si no tiene servicios ni categoría específica, aplica a todos
        return True
