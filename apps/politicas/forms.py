from django import forms
from .models import PoliticaCancelacion, PoliticaReembolso

class PoliticaCancelacionForm(forms.ModelForm):
    """Formulario para políticas de cancelación (CU-25)"""
    class Meta:
        model = PoliticaCancelacion
        fields = ['titulo', 'descripcion', 'horas_anticipacion', 'penalizacion_porcentaje', 'activa']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }


class PoliticaReembolsoForm(forms.ModelForm):
    """Formulario para políticas de reembolso (CU-19, CU-22)"""
    class Meta:
        model = PoliticaReembolso
        fields = ['titulo', 'descripcion', 'dias_reembolso', 'porcentaje_reembolso', 'condiciones', 'activa']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'condiciones': forms.Textarea(attrs={'rows': 4}),
        }


class BuscarPoliticaForm(forms.Form):
    """Formulario para buscar políticas (CU-46)"""
    tipo = forms.ChoiceField(
        choices=[('', 'Todas'), ('cancelacion', 'Cancelación'), ('reembolso', 'Reembolso')],
        required=False,
        label='Tipo de política'
    )
    activa = forms.BooleanField(required=False, label='Solo activas')
