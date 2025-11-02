from django import forms
from .models import Promocion

class PromocionForm(forms.ModelForm):
    """Formulario para registrar/modificar promoción (CU-18, CU-19)"""
    class Meta:
        model = Promocion
        fields = ['titulo', 'descripcion', 'tipo_descuento', 'valor_descuento', 
                  'categoria', 'servicios', 'fecha_inicio', 'fecha_fin', 'activa', 'codigo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'servicios': forms.CheckboxSelectMultiple(),
        }


class BuscarPromocionForm(forms.Form):
    """Formulario para buscar promoción (CU-45)"""
    titulo = forms.CharField(max_length=200, required=False, label='Buscar por título')
    codigo = forms.CharField(max_length=50, required=False, label='Código de promoción')
    activa = forms.BooleanField(required=False, label='Solo activas')
