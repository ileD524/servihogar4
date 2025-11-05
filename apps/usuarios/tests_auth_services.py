"""
Tests para los servicios de autenticación.
Cubre los casos de uso CU-07 (Iniciar Sesión) y CU-08 (Cerrar Sesión).
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock

from .auth_services import AuthService
from .models import Cliente, Profesional
from apps.servicios.models import Categoria, Servicio

Usuario = get_user_model()


class LoginEmailPasswordTestCase(TestCase):
    """Tests para CU-07: Iniciar Sesión con Email/Password"""
    
    def setUp(self):
        """Configuración inicial"""
        self.factory = RequestFactory()
        
        # Crear usuario activo
        self.usuario_activo = Usuario.objects.create_user(
            username='usuario_activo',
            email='activo@test.com',
            password='Password123!',
            first_name='Usuario',
            last_name='Activo',
            is_active=True
        )
        Cliente.objects.create(usuario=self.usuario_activo)
        
        # Crear usuario inactivo
        self.usuario_inactivo = Usuario.objects.create_user(
            username='usuario_inactivo',
            email='inactivo@test.com',
            password='Password123!',
            is_active=False
        )
    
    def test_login_exitoso(self):
        """Test: Login exitoso con credenciales correctas"""
        resultado = AuthService.login_email_password(
            email='activo@test.com',
            password='Password123!'
        )
        
        self.assertIn('usuario', resultado)
        self.assertIn('tokens', resultado)
        self.assertEqual(resultado['usuario']['email'], 'activo@test.com')
        self.assertEqual(resultado['usuario']['rol'], 'cliente')
        
        # Verificar que se generaron tokens
        self.assertIn('access', resultado['tokens'])
        self.assertIn('refresh', resultado['tokens'])
    
    def test_login_email_incorrecto(self):
        """Test: Login con email inexistente"""
        with self.assertRaises(ValueError) as context:
            AuthService.login_email_password(
                email='noexiste@test.com',
                password='Password123!'
            )
        
        self.assertIn('Credenciales inválidas', str(context.exception))
    
    def test_login_password_incorrecta(self):
        """Test: Login con contraseña incorrecta"""
        with self.assertRaises(ValueError) as context:
            AuthService.login_email_password(
                email='activo@test.com',
                password='PasswordIncorrecta!'
            )
        
        self.assertIn('Credenciales inválidas', str(context.exception))
    
    def test_login_usuario_inactivo(self):
        """Test: No puede hacer login un usuario inactivo"""
        with self.assertRaises(ValueError) as context:
            AuthService.login_email_password(
                email='inactivo@test.com',
                password='Password123!'
            )
        
        self.assertIn('desactivada', str(context.exception))
    
    def test_rate_limiting_intentos_fallidos(self):
        """Test: Bloqueo tras múltiples intentos fallidos"""
        email = 'activo@test.com'
        
        # Hacer 5 intentos fallidos
        for _ in range(5):
            try:
                AuthService.login_email_password(
                    email=email,
                    password='PasswordIncorrecta!'
                )
            except ValueError:
                pass
        
        # El sexto intento debe estar bloqueado
        with self.assertRaises(ValueError) as context:
            AuthService.login_email_password(
                email=email,
                password='Password123!'  # Incluso con la correcta
            )
        
        self.assertIn('bloqueado', str(context.exception).lower())
        self.assertIn('intentos', str(context.exception).lower())
    
    def test_reset_intentos_tras_login_exitoso(self):
        """Test: Los intentos fallidos se resetean tras login exitoso"""
        email = 'activo@test.com'
        
        # Hacer 3 intentos fallidos
        for _ in range(3):
            try:
                AuthService.login_email_password(
                    email=email,
                    password='PasswordIncorrecta!'
                )
            except ValueError:
                pass
        
        # Login exitoso
        resultado = AuthService.login_email_password(
            email=email,
            password='Password123!'
        )
        
        self.assertIsNotNone(resultado)
        
        # Verificar que los intentos se resetearon
        # (no debería haber registro de intentos fallidos)
        self.assertNotIn(email, AuthService._failed_attempts)
    
    def test_actualiza_last_login(self):
        """Test: Se actualiza la fecha de último login"""
        usuario = Usuario.objects.get(email='activo@test.com')
        last_login_antes = usuario.last_login
        
        AuthService.login_email_password(
            email='activo@test.com',
            password='Password123!'
        )
        
        usuario.refresh_from_db()
        self.assertIsNotNone(usuario.last_login)
        
        if last_login_antes:
            self.assertGreater(usuario.last_login, last_login_antes)


class LoginGoogleTestCase(TestCase):
    """Tests para CU-07: Iniciar Sesión con Google OAuth"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear usuario con Google ID
        self.usuario_google = Usuario.objects.create_user(
            username='usuario_google',
            email='google@test.com',
            password='',  # Sin contraseña (solo Google)
            first_name='Usuario',
            last_name='Google',
            google_id='12345678901234567890',
            is_active=True
        )
        Cliente.objects.create(usuario=self.usuario_google)
        
        # Crear usuario sin Google ID
        self.usuario_normal = Usuario.objects.create_user(
            username='usuario_normal',
            email='normal@test.com',
            password='Password123!',
            is_active=True
        )
    
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_exitoso(self, mock_verify):
        """Test: Login exitoso con Google OAuth"""
        # Mockear respuesta de Google
        mock_verify.return_value = {
            'sub': '12345678901234567890',
            'email': 'google@test.com',
            'email_verified': True,
            'given_name': 'Usuario',
            'family_name': 'Google',
            'picture': 'https://example.com/photo.jpg'
        }
        
        resultado = AuthService.login_google(
            google_token='fake-google-token'
        )
        
        self.assertIn('usuario', resultado)
        self.assertIn('tokens', resultado)
        self.assertEqual(resultado['usuario']['email'], 'google@test.com')
        self.assertEqual(resultado['usuario']['rol'], 'cliente')
    
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_vincula_cuenta_existente(self, mock_verify):
        """Test: Vincula cuenta existente sin Google ID"""
        mock_verify.return_value = {
            'sub': '99999999999999999999',
            'email': 'normal@test.com',
            'email_verified': True,
            'given_name': 'Usuario',
            'family_name': 'Normal'
        }
        
        resultado = AuthService.login_google(
            google_token='fake-google-token'
        )
        
        self.assertIsNotNone(resultado)
        
        # Verificar que se vinculó el google_id
        usuario = Usuario.objects.get(email='normal@test.com')
        self.assertEqual(usuario.google_id, '99999999999999999999')
    
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_email_no_verificado(self, mock_verify):
        """Test: No permite login con email no verificado"""
        mock_verify.return_value = {
            'sub': '12345678901234567890',
            'email': 'google@test.com',
            'email_verified': False,  # No verificado
            'given_name': 'Usuario',
            'family_name': 'Google'
        }
        
        with self.assertRaises(ValueError) as context:
            AuthService.login_google(google_token='fake-google-token')
        
        self.assertIn('verificado', str(context.exception).lower())
    
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_usuario_no_registrado(self, mock_verify):
        """Test: No permite login de usuario no registrado"""
        mock_verify.return_value = {
            'sub': '88888888888888888888',
            'email': 'noregistrado@test.com',
            'email_verified': True,
            'given_name': 'No',
            'family_name': 'Registrado'
        }
        
        with self.assertRaises(ValueError) as context:
            AuthService.login_google(google_token='fake-google-token')
        
        self.assertIn('no registrado', str(context.exception).lower())
    
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_token_invalido(self, mock_verify):
        """Test: Manejo de token de Google inválido"""
        mock_verify.side_effect = Exception("Invalid token")
        
        with self.assertRaises(ValueError) as context:
            AuthService.login_google(google_token='invalid-token')
        
        self.assertIn('inválido', str(context.exception).lower())


class LogoutTestCase(TestCase):
    """Tests para CU-08: Cerrar Sesión"""
    
    def setUp(self):
        """Configuración inicial"""
        self.factory = RequestFactory()
        
        self.usuario = Usuario.objects.create_user(
            username='usuario_test',
            email='test@test.com',
            password='Password123!',
            is_active=True
        )
    
    def test_logout_exitoso(self):
        """Test: Logout exitoso"""
        resultado = AuthService.logout_user(
            usuario=self.usuario,
            refresh_token='fake-refresh-token'
        )
        
        self.assertTrue(resultado['success'])
        self.assertIn('exitoso', resultado['mensaje'].lower())
    
    def test_logout_invalida_refresh_token(self):
        """Test: Logout invalida el refresh token"""
        refresh_token = 'my-refresh-token'
        
        # Logout
        AuthService.logout_user(
            usuario=self.usuario,
            refresh_token=refresh_token
        )
        
        # Verificar que el token está en blacklist
        self.assertTrue(AuthService.is_token_blacklisted(refresh_token))
    
    def test_logout_sin_refresh_token(self):
        """Test: Logout sin proporcionar refresh token"""
        resultado = AuthService.logout_user(
            usuario=self.usuario,
            refresh_token=None
        )
        
        self.assertTrue(resultado['success'])
    
    def test_logout_con_request_django(self):
        """Test: Logout con sesión Django"""
        request = self.factory.post('/logout/')
        request.user = self.usuario
        
        # Simular que el usuario está autenticado
        request.user.is_authenticated = True
        
        resultado = AuthService.logout_user(
            usuario=self.usuario,
            request=request
        )
        
        self.assertTrue(resultado['success'])


class TokenManagementTestCase(TestCase):
    """Tests para gestión de tokens"""
    
    def setUp(self):
        """Configuración inicial"""
        self.usuario = Usuario.objects.create_user(
            username='usuario_test',
            email='test@test.com',
            password='Password123!',
            is_active=True
        )
        Cliente.objects.create(usuario=self.usuario)
    
    def test_genera_tokens_jwt(self):
        """Test: Genera tokens JWT correctamente"""
        tokens = AuthService._generate_tokens(self.usuario)
        
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)
        self.assertIsInstance(tokens['access'], str)
        self.assertIsInstance(tokens['refresh'], str)
        self.assertGreater(len(tokens['access']), 50)
        self.assertGreater(len(tokens['refresh']), 50)
    
    def test_identifica_rol_cliente(self):
        """Test: Identifica correctamente rol de cliente"""
        rol = AuthService._get_user_role(self.usuario)
        self.assertEqual(rol, 'cliente')
    
    def test_identifica_rol_profesional(self):
        """Test: Identifica correctamente rol de profesional"""
        # Eliminar perfil de cliente
        Cliente.objects.filter(usuario=self.usuario).delete()
        
        # Crear categoría y servicio
        categoria = Categoria.objects.create(nombre='Test', descripcion='Test')
        servicio = Servicio.objects.create(
            nombre='Test',
            descripcion='Test',
            categoria=categoria,
            precio_base=50.00,
            duracion_estimada=120
        )
        
        # Crear perfil de profesional
        profesional = Profesional.objects.create(
            usuario=self.usuario,
            anios_experiencia=5
        )
        profesional.servicios.add(servicio)
        
        rol = AuthService._get_user_role(self.usuario)
        self.assertEqual(rol, 'profesional')
    
    def test_identifica_rol_administrador(self):
        """Test: Identifica correctamente rol de administrador"""
        admin = Usuario.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='Admin123!',
            is_staff=True,
            is_superuser=True
        )
        
        rol = AuthService._get_user_role(admin)
        self.assertEqual(rol, 'administrador')
    
    def test_blacklist_token(self):
        """Test: Agregar token a blacklist"""
        token = 'test-token-123'
        
        # Verificar que no está en blacklist
        self.assertFalse(AuthService.is_token_blacklisted(token))
        
        # Agregar a blacklist
        AuthService._blacklist_token(token)
        
        # Verificar que está en blacklist
        self.assertTrue(AuthService.is_token_blacklisted(token))
    
    def test_get_remaining_lockout_time(self):
        """Test: Obtener tiempo restante de bloqueo"""
        email = 'test@test.com'
        
        # Sin bloqueo
        remaining = AuthService._get_remaining_lockout_time(email)
        self.assertEqual(remaining, 0)
        
        # Simular bloqueo
        AuthService._lockout_times[email] = timezone.now()
        
        # Debe haber tiempo restante
        remaining = AuthService._get_remaining_lockout_time(email)
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, AuthService.LOCKOUT_DURATION_MINUTES)
