from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.usuarios.models import Cliente, Profesional
from apps.servicios.models import Servicio
from apps.promociones.models import Promocion

class Turno(models.Model):
    """Turnos solicitados por clientes"""
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('en_curso', 'En Curso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='turnos')
    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name='turnos')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='turnos')
    promocion = models.ForeignKey(Promocion, on_delete=models.SET_NULL, related_name='turnos', blank=True, null=True)
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(default=timezone.now)
    direccion_servicio = models.TextField()
    latitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    observaciones = models.TextField(blank=True, null=True)
    precio_final = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['-fecha', '-hora']
        
    def __str__(self):
        return f"Turno #{self.id} - {self.servicio.nombre} - {self.estado}"
    
    def buscar_promociones_aplicables(self):
        """Busca todas las promociones que aplican a este turno"""
        from django.utils import timezone
        now = timezone.now()
        
        # Buscar promociones vigentes que apliquen al servicio
        promociones = Promocion.objects.filter(
            activa=True,
            fecha_inicio__lte=now,
            fecha_fin__gte=now
        )
        
        promociones_validas = []
        for promo in promociones:
            if promo.aplica_a_servicio(self.servicio):
                promociones_validas.append(promo)
        
        return promociones_validas
    
    def calcular_precio_base(self):
        """Calcula el precio base del servicio"""
        return self.servicio.precio
    
    def calcular_descuento(self):
        """Calcula el descuento aplicado si hay promoción"""
        if self.promocion and self.promocion.esta_vigente():
            return self.promocion.calcular_descuento(self.calcular_precio_base())
        return 0
    
    def calcular_precio_final(self):
        """Calcula el precio final con descuento aplicado"""
        precio_base = self.calcular_precio_base()
        descuento = self.calcular_descuento()
        return precio_base - descuento
    
    def aplicar_promocion_automatica(self):
        """Aplica automáticamente la mejor promoción disponible"""
        promociones = self.buscar_promociones_aplicables()
        
        if not promociones:
            self.promocion = None
            self.precio_final = self.calcular_precio_base()
            return None
        
        # Encontrar la promoción con mayor descuento
        mejor_promocion = None
        mayor_descuento = 0
        
        precio_base = self.calcular_precio_base()
        for promo in promociones:
            descuento = promo.calcular_descuento(precio_base)
            if descuento > mayor_descuento:
                mayor_descuento = descuento
                mejor_promocion = promo
        
        self.promocion = mejor_promocion
        self.precio_final = self.calcular_precio_final()
        return mejor_promocion


class Pago(models.Model):
    """Pagos de turnos"""
    METODOS = (
        ('efectivo', 'Efectivo'),
        ('mercadopago', 'Mercado Pago'),
        ('transferencia', 'Transferencia'),
    )
    
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
    )
    
    turno = models.OneToOneField(Turno, on_delete=models.CASCADE, related_name='pago')
    metodo = models.CharField(max_length=20, choices=METODOS)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    mercadopago_id = models.CharField(max_length=255, blank=True, null=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        
    def __str__(self):
        return f"Pago #{self.id} - Turno #{self.turno.id} - {self.estado}"

class Calificacion(models.Model):
    """Calificación asociada a un turno"""
    turno = models.ForeignKey('Turno', on_delete=models.CASCADE, related_name='calificaciones')
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calificaciones_realizadas')
    puntuacion = models.PositiveSmallIntegerField(default=5, help_text='Puntuación de 1 a 5')
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        ordering = ['-fecha']

    def __str__(self):
        return f'Calificación {self.puntuacion}/5 - Turno #{self.turno_id}'
