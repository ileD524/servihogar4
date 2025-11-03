from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Cliente, Profesional
from apps.servicios.models import Servicio

class RegistroUsuarioForm(UserCreationForm):
    """Formulario de registro de usuarios - Solo Cliente y Profesional (CU-01)"""
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=False)
    direccion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    # Choices solo para cliente y profesional (NO administrador)
    ROL_CHOICES = (
        ('cliente', 'Cliente'),
        ('profesional', 'Profesional'),
    )
    
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=True, label='Tipo de Usuario')
    
    # Campos adicionales para profesionales
    servicios = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.filter(activo=True, categoria__activa=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Servicios que ofrece'
    )
    
    anios_experiencia = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        label='Años de experiencia',
        help_text='Solo para profesionales'
    )
    
    # Campos para horarios (se procesarán con JavaScript en el template)
    horarios_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 
                  'rol', 'telefono', 'direccion']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Crear perfil según el rol
            if user.rol == 'cliente':
                Cliente.objects.create(usuario=user)
            elif user.rol == 'profesional':
                profesional = Profesional.objects.create(
                    usuario=user,
                    anios_experiencia=self.cleaned_data.get('anios_experiencia', 0)
                )
                
                # Asignar servicios seleccionados al perfil profesional
                servicios = self.cleaned_data.get('servicios', [])
                for servicio in servicios:
                    servicio.profesional = profesional
                    servicio.save()
        return user


class ModificarUsuarioForm(forms.ModelForm):
    """Formulario de modificación de usuarios (CU-03 y CU-05)"""
    
    # Choices para rol (solo cliente y profesional, no administrador)
    ROL_CHOICES = (
        ('cliente', 'Cliente'),
        ('profesional', 'Profesional'),
    )
    
    rol = forms.ChoiceField(
        choices=ROL_CHOICES,
        required=True,
        label='Rol',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Campos adicionales para profesionales
    servicios = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.filter(activo=True, categoria__activa=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Servicios que ofrece'
    )
    
    anios_experiencia = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        label='Años de experiencia',
        help_text='Solo para profesionales'
    )
    
    # Campo oculto para horarios
    horarios_json = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion', 'foto_perfil', 'rol', 'activo']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        # Extraer el usuario que está editando (quien hace la petición)
        self.editor_user = kwargs.pop('editor_user', None)
        super().__init__(*args, **kwargs)
        
        instance = kwargs.get('instance')
        
        # Si editor_user es None, significa que el usuario se está editando a sí mismo
        # En ese caso, ocultar campos de administrador (rol, activo)
        if self.editor_user is None:
            if 'activo' in self.fields:
                del self.fields['activo']
            if 'rol' in self.fields:
                del self.fields['rol']
        
        # Eliminar completamente campos sensibles si el usuario que se está editando es administrador
        elif instance and instance.rol == 'administrador':
            # Los administradores no pueden cambiar su estado 'activo' ni su rol
            if 'activo' in self.fields:
                del self.fields['activo']
            if 'rol' in self.fields:
                del self.fields['rol']
            
        # Precargar servicios y años de experiencia si tiene perfil profesional
        # (aunque el rol actual sea cliente, para mantener los datos)
        if instance:
            try:
                # Intentar obtener el perfil profesional aunque el rol sea cliente
                if hasattr(instance, 'perfil_profesional'):
                    profesional = instance.perfil_profesional
                    # Filtrar servicios donde el profesional es este perfil
                    servicios_actuales = Servicio.objects.filter(profesional=profesional)
                    self.fields['servicios'].initial = [s.id for s in servicios_actuales]
                    # Precargar años de experiencia
                    self.fields['anios_experiencia'].initial = profesional.anios_experiencia
            except:
                # Si no tiene perfil profesional, no precargar nada
                pass


class RegistrarUsuarioAdminForm(forms.ModelForm):
    """Formulario para que el ADMINISTRADOR registre usuarios (CU-04)"""
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese contraseña'}),
        help_text='Mínimo 8 caracteres'
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme contraseña'})
    )
    
    # Solo Cliente y Profesional
    ROL_CHOICES = (
        ('cliente', 'Cliente'),
        ('profesional', 'Profesional'),
    )
    
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=True, label='Tipo de Usuario')
    
    # Campos adicionales para profesionales
    especialidades = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Solo para profesionales'
    )
    anios_experiencia = forms.IntegerField(
        min_value=0,
        required=False,
        help_text='Solo para profesionales'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'rol', 
                  'telefono', 'direccion', 'foto_perfil']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return password2
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso')
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.activo = True
        
        if commit:
            user.save()
            # Crear perfil según el rol
            if user.rol == 'cliente':
                Cliente.objects.create(usuario=user)
            elif user.rol == 'profesional':
                Profesional.objects.create(
                    usuario=user,
                    especialidades=self.cleaned_data.get('especialidades', ''),
                    anios_experiencia=self.cleaned_data.get('anios_experiencia', 0)
                )
        return user


class BuscarUsuarioForm(forms.Form):
    """Formulario para buscar usuarios (CU-42)"""
    nombre = forms.CharField(max_length=100, required=False, label='Nombre')
    apellido = forms.CharField(max_length=100, required=False, label='Apellido')
    
    ROL_CHOICES = (
        ('', 'Todos'),
        ('cliente', 'Cliente'),
        ('profesional', 'Profesional'),
        ('administrador', 'Administrador'),
    )
    rol = forms.ChoiceField(choices=ROL_CHOICES, required=False, label='Rol')
    
    ESTADO_CHOICES = (
        ('', 'Todos'),
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )
    estado = forms.ChoiceField(choices=ESTADO_CHOICES, required=False, label='Estado')


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión (CU-07)"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Usuario'}),
        label='Usuario'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
        label='Contraseña'
    )


class ModificarPerfilClienteForm(forms.ModelForm):
    """Formulario para modificar perfil de cliente"""
    class Meta:
        model = Cliente
        fields = ['preferencias']
        widgets = {
            'preferencias': forms.Textarea(attrs={'rows': 4}),
        }


class ModificarPerfilProfesionalForm(forms.ModelForm):
    """Formulario para modificar perfil de profesional"""
    class Meta:
        model = Profesional
        fields = ['especialidades', 'anios_experiencia', 'certificaciones', 
                  'disponible', 'radio_cobertura_km']
        widgets = {
            'especialidades': forms.Textarea(attrs={'rows': 3}),
            'certificaciones': forms.Textarea(attrs={'rows': 3}),
        }
