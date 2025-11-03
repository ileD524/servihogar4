from django import forms
from .models import Turno, Pago, Calificacion
from apps.servicios.models import Servicio, Categoria

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
        super().__init__(*args, **kwargs)
        # Los campos fecha, hora y servicio se manejarán dinámicamente con JavaScript
        # No los incluimos en el formulario porque se seleccionan desde la grilla


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