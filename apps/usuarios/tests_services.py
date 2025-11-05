"""
Tests unitarios para los servicios de gestión de usuarios.
Ejemplos de cómo probar la lógica de negocio de los casos de uso CU-01, CU-02, CU-03.

Para ejecutar:
    python manage.py test apps.usuarios.tests_services
"""
from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.usuarios.models import Cliente, Profesional, HorarioDisponibilidad
from apps.usuarios.services import UsuarioService
from apps.usuarios.validators import UsuarioValidator, PerfilValidator

Usuario = get_user_model()


class UsuarioValidatorTestCase(TestCase):
    """
    Tests para validaciones de usuario.
    Verifica que las validaciones de negocio funcionen correctamente.
    """
    
    def test_validar_email_formato_valido(self):
        """El validador debe aceptar emails con formato válido"""
        emails_validos = [
            'usuario@example.com',
            'nombre.apellido@empresa.com.ar',
            'admin+test@domain.co',
        ]
        
        for email in emails_validos:
            try:
                UsuarioValidator.validar_email_formato(email)
            except ValidationError:
                self.fail(f"Email válido rechazado: {email}")
    
    def test_validar_email_formato_invalido(self):
        """El validador debe rechazar emails con formato inválido"""
        emails_invalidos = [
            'usuario@',
            '@example.com',
            'usuario @example.com',
            'usuario',
            '',
        ]
        
        for email in emails_invalidos:
            with self.assertRaises(ValidationError):
                UsuarioValidator.validar_email_formato(email)
    
    def test_validar_contrasena_segura_valida(self):
        """El validador debe aceptar contraseñas seguras"""
        passwords_validas = [
            'Segura123',
            'MiContraseña456!',
            'PassWord789',
        ]
        
        for password in passwords_validas:
            try:
                UsuarioValidator.validar_contrasena_segura(password)
            except ValidationError:
                self.fail(f"Contraseña válida rechazada: {password}")
    
    def test_validar_contrasena_segura_invalida(self):
        """El validador debe rechazar contraseñas débiles"""
        passwords_invalidas = [
            'password',  # Sin mayúscula ni número
            'PASSWORD123',  # Sin minúscula
            'Password',  # Sin número
            'Pass1',  # Muy corta
            '12345678',  # Solo números
        ]
        
        for password in passwords_invalidas:
            with self.assertRaises(ValidationError):
                UsuarioValidator.validar_contrasena_segura(password)
    
    def test_validar_telefono_valido(self):
        """El validador debe aceptar teléfonos con formato válido"""
        telefonos_validos = [
            '+54 11 1234-5678',
            '(011) 9876-5432',
            '1234567890',
            '+1-555-123-4567',
        ]
        
        for telefono in telefonos_validos:
            try:
                UsuarioValidator.validar_telefono(telefono)
            except ValidationError:
                self.fail(f"Teléfono válido rechazado: {telefono}")
    
    def test_validar_telefono_invalido(self):
        """El validador debe rechazar teléfonos con formato inválido"""
        telefonos_invalidos = [
            '12345',  # Muy corto
            'abc123',  # Letras
            '+++',  # Solo símbolos
        ]
        
        for telefono in telefonos_invalidos:
            with self.assertRaises(ValidationError):
                UsuarioValidator.validar_telefono(telefono)
    
    def test_validar_horarios_validos(self):
        """El validador debe aceptar horarios con formato válido"""
        horarios_validos = [
            [
                {'dia': 'lunes', 'hora_inicio': '09:00', 'hora_fin': '18:00'},
                {'dia': 'martes', 'hora_inicio': '09:00', 'hora_fin': '18:00'},
            ]
        ]
        
        for horarios in horarios_validos:
            try:
                UsuarioValidator.validar_horarios(horarios)
            except ValidationError:
                self.fail("Horarios válidos rechazados")
    
    def test_validar_horarios_invalidos(self):
        """El validador debe rechazar horarios con formato inválido"""
        # Horarios vacíos
        with self.assertRaises(ValidationError):
            UsuarioValidator.validar_horarios([])
        
        # Hora de inicio mayor que hora de fin
        with self.assertRaises(ValidationError):
            UsuarioValidator.validar_horarios([
                {'dia': 'lunes', 'hora_inicio': '18:00', 'hora_fin': '09:00'}
            ])
        
        # Día inválido
        with self.assertRaises(ValidationError):
            UsuarioValidator.validar_horarios([
                {'dia': 'lunees', 'hora_inicio': '09:00', 'hora_fin': '18:00'}
            ])


class RegistrarUsuarioServiceTestCase(TestCase):
    """
    Tests para el servicio de registro de usuarios (CU-01).
    """
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.factory = RequestFactory()
    
    def test_registrar_cliente_exitoso(self):
        """Debe registrar un cliente correctamente"""
        datos_usuario = {
            'username': 'cliente_test',
            'email': 'cliente@test.com',
            'password': 'TestPass123!',
            'first_name': 'Cliente',
            'last_name': 'Test',
            'telefono': '+54 11 1234-5678',
            'direccion': 'Dirección Test',
            'rol': 'cliente',
        }
        
        request = self.factory.post('/registro/')
        usuario, errores = UsuarioService.registrar_usuario_manual(
            datos_usuario, 
            None, 
            request
        )
        
        # Verificar que no hay errores
        self.assertEqual(len(errores), 0)
        
        # Verificar que el usuario fue creado
        self.assertIsNotNone(usuario.id)
        self.assertEqual(usuario.username, 'cliente_test')
        self.assertEqual(usuario.email, 'cliente@test.com')
        self.assertEqual(usuario.rol, 'cliente')
        
        # Verificar que el usuario está inactivo (pendiente de confirmación)
        self.assertFalse(usuario.activo)
        self.assertFalse(usuario.is_active)
        
        # Verificar que se creó el perfil de cliente
        self.assertTrue(hasattr(usuario, 'perfil_cliente'))
    
    def test_registrar_profesional_exitoso(self):
        """Debe registrar un profesional correctamente"""
        datos_usuario = {
            'username': 'profesional_test',
            'email': 'profesional@test.com',
            'password': 'TestPass456!',
            'first_name': 'Profesional',
            'last_name': 'Test',
            'telefono': '+54 11 9876-5432',
            'direccion': 'Dirección Test',
            'rol': 'profesional',
        }
        
        datos_perfil = {
            'anios_experiencia': 5,
            'servicios': [],
            'horarios': [
                {'dia': 'lunes', 'hora_inicio': '09:00', 'hora_fin': '18:00'},
                {'dia': 'martes', 'hora_inicio': '09:00', 'hora_fin': '18:00'},
            ],
        }
        
        request = self.factory.post('/registro/')
        usuario, errores = UsuarioService.registrar_usuario_manual(
            datos_usuario, 
            datos_perfil, 
            request
        )
        
        # Verificar que no hay errores
        self.assertEqual(len(errores), 0)
        
        # Verificar que el usuario fue creado
        self.assertIsNotNone(usuario.id)
        self.assertEqual(usuario.rol, 'profesional')
        
        # Verificar que se creó el perfil de profesional
        self.assertTrue(hasattr(usuario, 'perfil_profesional'))
        self.assertEqual(usuario.perfil_profesional.anios_experiencia, 5)
        
        # Verificar que se crearon los horarios
        horarios = HorarioDisponibilidad.objects.filter(
            profesional=usuario.perfil_profesional
        )
        self.assertEqual(horarios.count(), 2)
    
    def test_registrar_email_duplicado(self):
        """No debe permitir registrar un email duplicado"""
        # Crear primer usuario
        Usuario.objects.create_user(
            username='usuario1',
            email='duplicado@test.com',
            password='Pass123!'
        )
        
        # Intentar crear segundo usuario con mismo email
        datos_usuario = {
            'username': 'usuario2',
            'email': 'duplicado@test.com',
            'password': 'Pass456!',
            'first_name': 'Usuario',
            'last_name': 'Dos',
            'rol': 'cliente',
        }
        
        request = self.factory.post('/registro/')
        
        with self.assertRaises(ValidationError) as context:
            UsuarioService.registrar_usuario_manual(datos_usuario, None, request)
        
        # Verificar que el error menciona email duplicado
        self.assertIn('email', str(context.exception).lower())
    
    def test_registrar_contrasena_debil(self):
        """No debe permitir registrar con contraseña débil"""
        datos_usuario = {
            'username': 'usuario_test',
            'email': 'test@test.com',
            'password': '12345',  # Contraseña débil
            'first_name': 'Usuario',
            'last_name': 'Test',
            'rol': 'cliente',
        }
        
        request = self.factory.post('/registro/')
        
        with self.assertRaises(ValidationError) as context:
            UsuarioService.registrar_usuario_manual(datos_usuario, None, request)
        
        # Verificar que el error menciona contraseña
        self.assertIn('contraseña', str(context.exception).lower())
    
    def test_confirmar_email_exitoso(self):
        """Debe activar un usuario al confirmar email"""
        # Crear usuario inactivo
        usuario = Usuario.objects.create_user(
            username='usuario_test',
            email='test@test.com',
            password='Pass123!',
            rol='cliente',
            activo=False,
            is_active=False
        )
        Cliente.objects.create(usuario=usuario)
        
        # Confirmar email
        usuario_confirmado = UsuarioService.confirmar_email(usuario.id)
        
        # Verificar que el usuario está activo
        self.assertTrue(usuario_confirmado.activo)
        self.assertTrue(usuario_confirmado.is_active)


class ModificarPerfilServiceTestCase(TestCase):
    """
    Tests para el servicio de modificación de perfil (CU-03).
    """
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            username='usuario_test',
            email='test@test.com',
            password='Pass123!',
            first_name='Usuario',
            last_name='Test',
            rol='cliente',
            activo=True,
            is_active=True
        )
        Cliente.objects.create(usuario=self.usuario)
    
    def test_modificar_perfil_exitoso(self):
        """Debe modificar el perfil correctamente"""
        datos_actualizados = {
            'first_name': 'Usuario Modificado',
            'telefono': '+54 11 9999-9999',
            'direccion': 'Nueva dirección',
        }
        
        usuario_actualizado = UsuarioService.modificar_perfil(
            self.usuario.id,
            datos_actualizados
        )
        
        # Verificar cambios
        self.assertEqual(usuario_actualizado.first_name, 'Usuario Modificado')
        self.assertEqual(usuario_actualizado.telefono, '+54 11 9999-9999')
        self.assertEqual(usuario_actualizado.direccion, 'Nueva dirección')
    
    def test_modificar_email_duplicado(self):
        """No debe permitir cambiar a un email que ya existe"""
        # Crear otro usuario
        Usuario.objects.create_user(
            username='otro_usuario',
            email='otro@test.com',
            password='Pass123!'
        )
        
        # Intentar cambiar al email del otro usuario
        datos_actualizados = {
            'email': 'otro@test.com',
        }
        
        with self.assertRaises(ValidationError):
            UsuarioService.modificar_perfil(
                self.usuario.id,
                datos_actualizados
            )
    
    def test_modificar_email_propio(self):
        """Debe permitir 'cambiar' al mismo email (sin cambios reales)"""
        datos_actualizados = {
            'email': 'test@test.com',  # Mismo email
        }
        
        usuario_actualizado = UsuarioService.modificar_perfil(
            self.usuario.id,
            datos_actualizados
        )
        
        # No debe lanzar error
        self.assertEqual(usuario_actualizado.email, 'test@test.com')


class EliminarPerfilServiceTestCase(TestCase):
    """
    Tests para el servicio de eliminación de perfil (CU-02).
    """
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            username='usuario_test',
            email='test@test.com',
            password='Pass123!',
            first_name='Usuario',
            last_name='Test',
            rol='cliente',
            activo=True,
            is_active=True
        )
        Cliente.objects.create(usuario=self.usuario)
    
    def test_eliminar_perfil_sin_turnos(self):
        """Debe eliminar el perfil si no hay turnos activos"""
        resultado = UsuarioService.eliminar_perfil(self.usuario.id)
        
        # Verificar que fue exitoso
        self.assertTrue(resultado['success'])
        
        # Verificar que el usuario está inactivo
        usuario = Usuario.objects.get(id=self.usuario.id)
        self.assertFalse(usuario.activo)
        self.assertFalse(usuario.is_active)
        
        # Verificar anonimización
        self.assertEqual(usuario.first_name, 'Usuario')
        self.assertEqual(usuario.last_name, 'Eliminado')
        self.assertIn('eliminado_', usuario.email)
        self.assertIn('eliminado_', usuario.username)
    
    def test_puede_eliminar_perfil_sin_restricciones(self):
        """Debe permitir eliminar si no hay restricciones"""
        puede_eliminar, mensaje = PerfilValidator.puede_eliminar_perfil(self.usuario)
        
        self.assertTrue(puede_eliminar)
        self.assertIsNone(mensaje)
    
    def test_no_puede_eliminar_con_turnos_activos(self):
        """No debe permitir eliminar si hay turnos activos"""
        from apps.turnos.models import Turno
        from apps.servicios.models import Servicio, Categoria
        
        # Crear profesional
        profesional_user = Usuario.objects.create_user(
            username='profesional',
            email='prof@test.com',
            password='Pass123!',
            rol='profesional'
        )
        profesional = Profesional.objects.create(usuario=profesional_user)
        
        # Crear servicio
        categoria = Categoria.objects.create(nombre='Test')
        servicio = Servicio.objects.create(
            nombre='Servicio Test',
            categoria=categoria,
            profesional=profesional,
            precio=100
        )
        
        # Crear turno pendiente
        Turno.objects.create(
            cliente=self.usuario.perfil_cliente,
            profesional=profesional,
            servicio=servicio,
            direccion_servicio='Test',
            precio_final=100,
            estado='pendiente'
        )
        
        # Verificar que no puede eliminar
        puede_eliminar, mensaje = PerfilValidator.puede_eliminar_perfil(self.usuario)
        
        self.assertFalse(puede_eliminar)
        self.assertIsNotNone(mensaje)
        self.assertIn('turnos', mensaje.lower())


class RegistrarUsuarioGoogleTestCase(TestCase):
    """
    Tests para el registro con Google OAuth (CU-01).
    """
    
    def test_registrar_usuario_google_nuevo(self):
        """Debe crear un nuevo usuario con datos de Google"""
        google_data = {
            'google_id': '1234567890',
            'email': 'usuario@gmail.com',
            'first_name': 'Usuario',
            'last_name': 'Google',
        }
        
        usuario = UsuarioService.registrar_usuario_google(google_data)
        
        # Verificar que el usuario fue creado
        self.assertIsNotNone(usuario.id)
        self.assertEqual(usuario.email, 'usuario@gmail.com')
        self.assertEqual(usuario.google_id, '1234567890')
        
        # Verificar que está activo (no requiere confirmación)
        self.assertTrue(usuario.activo)
        self.assertTrue(usuario.is_active)
        
        # Verificar que no tiene contraseña usable
        self.assertFalse(usuario.has_usable_password())
    
    def test_registrar_usuario_google_existente(self):
        """Debe retornar el usuario existente con el mismo google_id"""
        # Crear usuario con Google
        google_data = {
            'google_id': '1234567890',
            'email': 'usuario@gmail.com',
            'first_name': 'Usuario',
            'last_name': 'Google',
        }
        
        usuario1 = UsuarioService.registrar_usuario_google(google_data)
        
        # Intentar registrar de nuevo con el mismo google_id
        usuario2 = UsuarioService.registrar_usuario_google(google_data)
        
        # Debe ser el mismo usuario
        self.assertEqual(usuario1.id, usuario2.id)
    
    def test_completar_datos_usuario_google(self):
        """Debe completar datos de usuario registrado con Google"""
        # Crear usuario con Google
        google_data = {
            'google_id': '1234567890',
            'email': 'usuario@gmail.com',
            'first_name': 'Usuario',
            'last_name': 'Google',
        }
        
        usuario = UsuarioService.registrar_usuario_google(google_data)
        
        # Completar datos
        datos_adicionales = {
            'telefono': '+54 11 1234-5678',
            'direccion': 'Dirección Test',
        }
        
        usuario_actualizado = UsuarioService.completar_datos_usuario_google(
            usuario.id,
            datos_adicionales
        )
        
        # Verificar cambios
        self.assertEqual(usuario_actualizado.telefono, '+54 11 1234-5678')
        self.assertEqual(usuario_actualizado.direccion, 'Dirección Test')


# Comando para ejecutar los tests:
# python manage.py test apps.usuarios.tests_services
