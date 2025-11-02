from django import forms
from .models import Servicio, Categoria
from apps.usuarios.models import Profesional


class BuscarServicioForm(forms.Form):
    """Formulario para buscar servicios (CU-39)"""
    nombre = forms.CharField(max_length=200, required=False, label='Nombre')
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label='Categoría',
        empty_label='Todos'
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos'), ('activo', 'Activo'), ('inactivo', 'Inactivo')],
        required=False,
        label='Estado'
    )


class BuscarCategoriaForm(forms.Form):
    """Formulario para buscar categorías (CU-40)"""
    nombre = forms.CharField(max_length=100, required=False, label='Nombre')
    estado = forms.ChoiceField(
        choices=[('', 'Todos'), ('activa', 'Activa'), ('inactiva', 'Inactiva')],
        required=False,
        label='Estado'
    )


class ServicioForm(forms.ModelForm):
    """Formulario para crear/editar servicios (CU-13, CU-15)"""
    
    class Meta:
        model = Servicio
        fields = ['categoria', 'nombre', 'descripcion', 'precio_base', 'duracion_estimada', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descripción del servicio'}),
            'precio_base': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'duracion_estimada': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Minutos'}),
        }
        labels = {
            'categoria': 'Categoría*',
            'nombre': 'Nombre del servicio*',
            'descripcion': 'Descripción*',
            'precio_base': 'Precio base*',
            'duracion_estimada': 'Duración estimada (minutos)*',
            'activo': 'Estado (activo/inactivo)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo categorías activas
        self.fields['categoria'].queryset = Categoria.objects.filter(activa=True)


class CategoriaForm(forms.ModelForm):
    """Formulario para crear/editar categorías (CU-36, CU-37)"""
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'activa']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción de la categoría'}),
        }
        labels = {
            'nombre': 'Nombre de la categoría*',
            'descripcion': 'Descripción*',
            'activa': 'Estado (activa/inactiva)'
        }