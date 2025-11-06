from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Promocion

class PromocionForm(forms.ModelForm):
    """Formulario para registrar/modificar promoción (CU-18, CU-19)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar categorías y servicios alfabéticamente
        from apps.servicios.models import Categoria, Servicio
        self.fields['categoria'].queryset = Categoria.objects.filter(activa=True).order_by('nombre')
        self.fields['servicios'].queryset = Servicio.objects.filter(activo=True).order_by('nombre')
        
        # Asegurar que el texto en los select sea visible
        self.fields['categoria'].widget.attrs.update({
            'style': 'color: #333 !important; background-color: #fff !important;'
        })
        self.fields['tipo_descuento'].widget.attrs.update({
            'style': 'color: #333 !important; background-color: #fff !important;'
        })
        
        # Formatear fechas para datetime-local cuando se está editando
        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio:
                # Convertir a formato datetime-local: YYYY-MM-DDTHH:MM
                fecha_inicio_local = timezone.localtime(self.instance.fecha_inicio)
                self.initial['fecha_inicio'] = fecha_inicio_local.strftime('%Y-%m-%dT%H:%M')
            
            if self.instance.fecha_fin:
                fecha_fin_local = timezone.localtime(self.instance.fecha_fin)
                self.initial['fecha_fin'] = fecha_fin_local.strftime('%Y-%m-%dT%H:%M')
    
    class Meta:
        model = Promocion
        fields = ['titulo', 'descripcion', 'tipo_descuento', 'valor_descuento', 
                  'categoria', 'servicios', 'fecha_inicio', 'fecha_fin', 'activa', 'codigo']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la promoción',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada de la promoción'
            }),
            'tipo_descuento': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'valor_descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Valor del descuento',
                'min': '0',
                'step': '0.01',
                'required': True
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control',
                'help_text': 'Dejar vacío para aplicar a todos los servicios'
            }),
            'servicios': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'fecha_inicio': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'required': True
            }),
            'fecha_fin': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'required': True
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único de la promoción (opcional)',
                'maxlength': '50'
            }),
        }
        labels = {
            'titulo': 'Nombre de la Promoción *',
            'descripcion': 'Descripción',
            'tipo_descuento': 'Tipo de Descuento *',
            'valor_descuento': 'Valor del Descuento *',
            'categoria': 'Categoría de Aplicación',
            'servicios': 'Servicios Específicos',
            'fecha_inicio': 'Fecha y Hora de Inicio *',
            'fecha_fin': 'Fecha y Hora de Fin *',
            'activa': 'Promoción Activa',
            'codigo': 'Código Promocional',
        }
        help_texts = {
            'categoria': 'Si no selecciona categoría, se aplicará a todos los servicios',
            'servicios': 'Seleccione servicios específicos o deje vacío para aplicar a toda la categoría',
            'codigo': 'Código único que los clientes pueden usar para aplicar la promoción',
        }
    
    def clean_valor_descuento(self):
        """Validar que el valor del descuento esté dentro de límites permitidos"""
        valor = self.cleaned_data.get('valor_descuento')
        tipo = self.cleaned_data.get('tipo_descuento')
        
        if valor is None:
            raise ValidationError('El valor del descuento es obligatorio')
        
        if valor <= 0:
            raise ValidationError('El valor del descuento debe ser mayor a cero')
        
        # Validar porcentaje (no puede ser mayor a 100%)
        if tipo == 'porcentaje' and valor > 100:
            raise ValidationError('El porcentaje de descuento no puede ser mayor a 100%')
        
        # Validar monto fijo (límite razonable: $10,000)
        if tipo == 'monto_fijo' and valor > 10000:
            raise ValidationError('El descuento en monto fijo no puede exceder $10,000')
        
        return valor
    
    def clean_fecha_fin(self):
        """Validar que la fecha de fin sea posterior a la fecha de inicio"""
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        fecha_fin = self.cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')
            
            # Validar que las fechas no sean muy lejanas (máximo 1 año)
            diferencia = fecha_fin - fecha_inicio
            if diferencia.days > 365:
                raise ValidationError('El período de vigencia no puede exceder 1 año')
        
        return fecha_fin
    
    def clean_fecha_inicio(self):
        """Validar que la fecha de inicio no sea muy antigua"""
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        
        if fecha_inicio:
            # Permitir fechas desde hace máximo 30 días atrás
            hace_30_dias = timezone.now() - timezone.timedelta(days=30)
            if fecha_inicio < hace_30_dias:
                raise ValidationError('La fecha de inicio no puede ser anterior a 30 días desde hoy')
        
        return fecha_inicio
    
    def clean_codigo(self):
        """Validar que el código sea único si se proporciona"""
        codigo = self.cleaned_data.get('codigo')
        
        if codigo:
            # Convertir a mayúsculas
            codigo = codigo.upper().strip()
            
            # Validar formato (solo letras y números)
            if not codigo.replace('-', '').replace('_', '').isalnum():
                raise ValidationError('El código solo puede contener letras, números, guiones y guiones bajos')
            
            # Verificar unicidad
            if self.instance.pk:
                # Modificación: excluir la instancia actual
                if Promocion.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
                    raise ValidationError(f'Ya existe una promoción con el código "{codigo}"')
            else:
                # Registro nuevo
                if Promocion.objects.filter(codigo=codigo).exists():
                    raise ValidationError(f'Ya existe una promoción con el código "{codigo}"')
        
        return codigo
    
    def clean(self):
        """Validaciones generales del formulario"""
        cleaned_data = super().clean()
        categoria = cleaned_data.get('categoria')
        servicios = cleaned_data.get('servicios')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        # Validar que si hay servicios seleccionados, pertenezcan a la categoría
        if categoria and servicios:
            for servicio in servicios:
                if servicio.categoria != categoria:
                    raise ValidationError(
                        f'El servicio "{servicio.nombre}" no pertenece a la categoría "{categoria.nombre}"'
                    )
        
        # Verificar solapamiento de promociones (opcional, según requerimientos)
        if fecha_inicio and fecha_fin and categoria:
            promociones_solapadas = Promocion.objects.filter(
                categoria=categoria,
                activa=True,
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio
            )
            
            # Si estamos editando, excluir la promoción actual
            if self.instance.pk:
                promociones_solapadas = promociones_solapadas.exclude(pk=self.instance.pk)
            
            if promociones_solapadas.exists():
                # Solo advertencia, no bloquear (puede haber múltiples promociones activas)
                self.add_warning = True
                self.warning_message = f'Atención: Existen {promociones_solapadas.count()} promoción(es) activa(s) en el mismo período para esta categoría'
        
        return cleaned_data


class BuscarPromocionForm(forms.Form):
    """Formulario para buscar promociones (CU-40)"""
    titulo = forms.CharField(max_length=100, required=False, label='Nombre')
    activa = forms.ChoiceField(
        choices=[('', 'Todos'), ('activa', 'Activa'), ('inactiva', 'Inactiva')],
        required=False,
        label='Estado'
    )
    fecha_inicio = forms.DateField(required=False, label='Fecha de Inicio', widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(required=False, label='Fecha de Fin', widget=forms.DateInput(attrs={'type': 'date'}))
