from django import forms
from .models import Turno, Pago, Calificacion
from apps.servicios.models import Servicio, Categoria
from apps.promociones.models import Promocion

class SolicitarTurnoForm(forms.ModelForm):
    """Formulario para solicitar turno (CU-23)"""
    # Campo para seleccionar servicio (agrupado por categoría)
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(activa=True),
        required=False,
        label='Categoría',
        empty_label='Seleccione una categoría',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_categoria'})
    )
    
    # Campo para código promocional
    codigo_promocion = forms.CharField(
        max_length=50,
        required=False,
        label='Código de promoción',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese código promocional (opcional)',
            'id': 'id_codigo_promocion'
        }),
        help_text='Si tienes un código promocional, ingrésalo aquí'
    )
    
    # Campo para seleccionar promoción de lista
    promocion = forms.ModelChoiceField(
        queryset=Promocion.objects.none(),
        required=False,
        label='Promoción disponible',
        empty_label='Sin promoción / Aplicar automáticamente',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_promocion'
        }),
        help_text='Selecciona una promoción o deja vacío para aplicar automáticamente la mejor'
    )
    
    class Meta:
        model = Turno
        fields = ['direccion_servicio', 'observaciones']
        widgets = {
            'direccion_servicio': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'id': 'id_direccion',
                'placeholder': 'La dirección se completará automáticamente al seleccionar en el mapa'
            }),
            'observaciones': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Ingrese observaciones adicionales para el profesional'
            }),
        }
        labels = {
            'direccion_servicio': 'Dirección del servicio',
            'observaciones': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        servicio = kwargs.pop('servicio', None)
        super().__init__(*args, **kwargs)
        
        # Si se proporciona un servicio, cargar promociones aplicables
        if servicio:
            from django.utils import timezone
            now = timezone.now()
            
            # Buscar promociones vigentes para este servicio
            promociones_vigentes = Promocion.objects.filter(
                activa=True,
                fecha_inicio__lte=now,
                fecha_fin__gte=now
            )
            
            # Filtrar las que aplican al servicio
            promociones_aplicables = []
            for promo in promociones_vigentes:
                if promo.aplica_a_servicio(servicio):
                    promociones_aplicables.append(promo.id)
            
            self.fields['promocion'].queryset = Promocion.objects.filter(
                id__in=promociones_aplicables
            )
    
    def clean_codigo_promocion(self):
        """Valida el código promocional si se ingresó"""
        codigo = self.cleaned_data.get('codigo_promocion', '').strip().upper()
        
        if not codigo:
            return None
        
        try:
            promocion = Promocion.objects.get(codigo__iexact=codigo)
            
            if not promocion.esta_vigente():
                raise forms.ValidationError(
                    'El código promocional ha expirado o no está activo.'
                )
            
            return promocion
        except Promocion.DoesNotExist:
            raise forms.ValidationError(
                'El código promocional ingresado no es válido.'
            )


class ModificarTurnoForm(forms.ModelForm):
    """Formulario para modificar turno (CU-24)"""
    class Meta:
        model = Turno
        fields = ['fecha', 'hora', 'direccion_servicio', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'direccion_servicio': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }


class BuscarTurnoForm(forms.Form):
    """Formulario para buscar turnos (CU-32)"""
    fecha_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    estado = forms.ChoiceField(choices=[('', 'Todos')] + list(Turno.ESTADOS), required=False)
    # Solo servicios activos con profesionales activos y categorías activas
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.filter(
            activo=True,
            profesional__usuario__activo=True,
            categoria__activa=True
        ).select_related('categoria', 'profesional__usuario'),
        required=False
    )


class ConfirmarTurnoForm(forms.ModelForm):
    """Formulario para que el profesional confirme el turno"""
    class Meta:
        model = Turno
        fields = ['estado', 'precio_final']
        widgets = {
            'estado': forms.Select(choices=[('confirmado', 'Confirmar'), ('cancelado', 'Rechazar')]),
        }


class PagoForm(forms.ModelForm):
    """Formulario para registrar pago"""
    class Meta:
        model = Pago
        fields = ['metodo', 'monto']

class CalificarTurnoForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'form-control',
                'placeholder': 'Puntuación (1-5)'
            }),
            'comentario': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Dejá tu comentario (opcional)'
            }),
        }
        labels = {
            'puntuacion': 'Puntuación',
            'comentario': 'Comentario'
        }