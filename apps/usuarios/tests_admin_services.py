"""
Tests para los servicios administrativos de usuarios.
Cubre los casos de uso CU-04, CU-05 y CU-06.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from .admin_services import AdminUsuarioService
from .models import Cliente, Profesional
from apps.servicios.models import Categoria, Servicio

Usuario = get_user_model()


class AdminRegistroUsuarioTestCase(TestCase):
    """Tests para CU-04: Registrar usuario (administrador)"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear administrador
        self.admin = Usuario.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='Admin123!',
            is_staff=True,
            is_superuser=True
        )
        
        # Crear categoría y servicios para profesionales
        self.categoria = Categoria.objects.create(
            nombre='Limpieza',
            descripcion='Servicios de limpieza'
        )
        
        self.servicio1 = Servicio.objects.create(
            nombre='Limpieza básica',
            descripcion='Limpieza general',
            categoria=self.categoria,
            precio_base=50.00,
            duracion_estimada=120
        )
        
        self.servicio2 = Servicio.objects.create(
            nombre='Limpieza profunda',
            descripcion='Limpieza a fondo',
            categoria=self.categoria,
            precio_base=100.00,
            duracion_estimada=240
        )
    
    def test_registrar_cliente_activo(self):
        """Test: registrar cliente directamente activo"""
        datos = {
            'username': 'cliente_nuevo',
            'email': 'cliente@test.com',
            'password': 'Cliente123!',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'telefono': '123456789',
            'rol': 'cliente',
            'estado': 'activo'
        }
        
        resultado = AdminUsuarioService.registrar_usuario_admin(datos, self.admin)
        
        self.assertIsNotNone(resultado['usuario'])
        self.assertEqual(resultado['rol'], 'cliente')
        self.assertTrue(resultado['usuario'].is_active)
        self.assertTrue(hasattr(resultado['usuario'], 'cliente'))
    
    def test_registrar_cliente_pendiente(self):
        """Test: registrar cliente en estado pendiente (debe confirmar email)"""
        datos = {
            'username': 'cliente_pendiente',
            'email': 'pendiente@test.com',
            'password': 'Cliente123!',
            'first_name': 'María',
            'last_name': 'García',
            'rol': 'cliente',
            'estado': 'pendiente'
        }
        
        resultado = AdminUsuarioService.registrar_usuario_admin(datos, self.admin)
        
        self.assertFalse(resultado['usuario'].is_active)
        self.assertFalse(resultado['usuario'].email_confirmado)
        self.assertTrue(resultado.get('requiere_confirmacion', False))
    
    def test_registrar_profesional_con_servicios(self):
        """Test: registrar profesional con servicios asignados"""
        datos = {
            'username': 'profesional_nuevo',
            'email': 'profesional@test.com',
            'password': 'Prof123!',
            'first_name': 'Carlos',
            'last_name': 'López',
            'telefono': '987654321',
            'rol': 'profesional',
            'estado': 'activo',
            'anios_experiencia': 5,
            'servicios': [self.servicio1.id, self.servicio2.id],
            'horarios': [
                {
                    'dia': 'lunes',
                    'hora_inicio': '09:00',
                    'hora_fin': '18:00'
                }
            ]
        }
        
        resultado = AdminUsuarioService.registrar_usuario_admin(datos, self.admin)
        
        self.assertEqual(resultado['rol'], 'profesional')
        profesional = resultado['usuario'].profesional
        self.assertEqual(profesional.anios_experiencia, 5)
        self.assertEqual(profesional.servicios.count(), 2)
    
    def test_registrar_profesional_sin_servicios_falla(self):
        """Test: no se puede registrar profesional sin servicios"""
        datos = {
            'username': 'profesional_sin_servicios',
            'email': 'prof_sin_servicios@test.com',
            'password': 'Prof123!',
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'rol': 'profesional',
            'estado': 'activo',
            'servicios': []  # Sin servicios
        }
        
        with self.assertRaises(ValueError) as context:
            AdminUsuarioService.registrar_usuario_admin(datos, self.admin)
        
        self.assertIn('servicios', str(context.exception).lower())
    
    def test_registrar_sin_password_genera_temporal(self):
        """Test: si no se proporciona password, se genera una temporal"""
        datos = {
            'username': 'sin_password',
            'email': 'sin_pass@test.com',
            'first_name': 'Pedro',
            'last_name': 'Sánchez',
            'rol': 'cliente',
            'estado': 'activo'
            # Sin password
        }
        
        resultado = AdminUsuarioService.registrar_usuario_admin(datos, self.admin)
        
        # El usuario debe poder autenticarse (se generó password)
        self.assertTrue(resultado['usuario'].has_usable_password())
    
    def test_registrar_email_duplicado_falla(self):
        """Test: no se puede registrar con email duplicado"""
        # Crear usuario existente
        Usuario.objects.create_user(
            username='existente',
            email='duplicado@test.com',
            password='Pass123!'
        )
        
        datos = {
            'username': 'nuevo',
            'email': 'duplicado@test.com',  # Email duplicado
            'password': 'Pass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'rol': 'cliente',
            'estado': 'activo'
        }
        
        with self.assertRaises(ValueError):
            AdminUsuarioService.registrar_usuario_admin(datos, self.admin)


class AdminModificarUsuarioTestCase(TestCase):
    """Tests para CU-05: Modificar usuario (administrador)"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin = Usuario.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='Admin123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.cliente = Usuario.objects.create_user(
            username='cliente',
            email='cliente@test.com',
            password='Cliente123!',
            first_name='Juan',
            last_name='Pérez'
        )
        Cliente.objects.create(usuario=self.cliente)
        
        # Crear categoría y servicio
        self.categoria = Categoria.objects.create(
            nombre='Limpieza',
            descripcion='Test'
        )
        self.servicio = Servicio.objects.create(
            nombre='Limpieza',
            descripcion='Test',
            categoria=self.categoria,
            precio_base=50.00,
            duracion_estimada=120
        )
    
    def test_modificar_datos_basicos(self):
        """Test: modificar datos básicos de un usuario"""
        datos = {
            'first_name': 'Carlos',
            'telefono': '111222333'
        }
        
        resultado = AdminUsuarioService.modificar_usuario_admin(
            self.cliente.id,
            datos,
            self.admin
        )
        
        usuario_actualizado = Usuario.objects.get(id=self.cliente.id)
        self.assertEqual(usuario_actualizado.first_name, 'Carlos')
        self.assertEqual(usuario_actualizado.telefono, '111222333')
    
    def test_activar_desactivar_usuario(self):
        """Test: el admin puede activar/desactivar usuarios"""
        # Desactivar
        datos = {'activo': False}
        AdminUsuarioService.modificar_usuario_admin(
            self.cliente.id,
            datos,
            self.admin
        )
        
        usuario = Usuario.objects.get(id=self.cliente.id)
        self.assertFalse(usuario.is_active)
        
        # Activar
        datos = {'activo': True}
        AdminUsuarioService.modificar_usuario_admin(
            self.cliente.id,
            datos,
            self.admin
        )
        
        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)
    
    def test_cambiar_rol_cliente_a_profesional(self):
        """Test: cambiar rol de cliente a profesional"""
        datos = {
            'rol': 'profesional',
            'servicios': [self.servicio.id],
            'anios_experiencia': 3
        }
        
        resultado = AdminUsuarioService.modificar_usuario_admin(
            self.cliente.id,
            datos,
            self.admin
        )
        
        usuario = Usuario.objects.get(id=self.cliente.id)
        self.assertEqual(resultado['rol'], 'profesional')
        self.assertTrue(hasattr(usuario, 'profesional'))
        self.assertFalse(hasattr(usuario, 'cliente'))
    
    def test_no_puede_modificar_otro_admin(self):
        """Test: un admin no puede modificar a otro admin"""
        otro_admin = Usuario.objects.create_user(
            username='admin2',
            email='admin2@test.com',
            password='Admin123!',
            is_staff=True,
            is_superuser=True
        )
        
        datos = {'first_name': 'Modificado'}
        
        with self.assertRaises(PermissionError):
            AdminUsuarioService.modificar_usuario_admin(
                otro_admin.id,
                datos,
                self.admin
            )
    
    def test_modificar_usuario_inexistente_falla(self):
        """Test: no se puede modificar usuario que no existe"""
        datos = {'first_name': 'Test'}
        
        with self.assertRaises(ValueError):
            AdminUsuarioService.modificar_usuario_admin(
                999999,  # ID inexistente
                datos,
                self.admin
            )


class AdminEliminarUsuarioTestCase(TestCase):
    """Tests para CU-06: Eliminar usuario (administrador)"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin = Usuario.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='Admin123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.cliente = Usuario.objects.create_user(
            username='cliente',
            email='cliente@test.com',
            password='Cliente123!',
            first_name='Juan',
            last_name='Pérez'
        )
        Cliente.objects.create(usuario=self.cliente)
    
    def test_eliminar_usuario_sin_turnos(self):
        """Test: eliminar usuario sin turnos activos"""
        usuario_id = self.cliente.id
        email_original = self.cliente.email
        
        resultado = AdminUsuarioService.eliminar_usuario_admin(
            usuario_id,
            self.admin,
            forzar=False
        )
        
        usuario = Usuario.objects.get(id=usuario_id)
        
        # Verificar eliminación lógica
        self.assertFalse(usuario.is_active)
        
        # Verificar anonimización
        self.assertNotEqual(usuario.email, email_original)
        self.assertTrue(usuario.email.startswith('eliminado_'))
    
    def test_eliminar_con_forzar(self):
        """Test: eliminar con flag forzar aunque haya condiciones"""
        resultado = AdminUsuarioService.eliminar_usuario_admin(
            self.cliente.id,
            self.admin,
            forzar=True
        )
        
        usuario = Usuario.objects.get(id=self.cliente.id)
        self.assertFalse(usuario.is_active)
    
    def test_no_puede_eliminar_otro_admin(self):
        """Test: no se puede eliminar a otro administrador"""
        otro_admin = Usuario.objects.create_user(
            username='admin2',
            email='admin2@test.com',
            password='Admin123!',
            is_staff=True,
            is_superuser=True
        )
        
        with self.assertRaises(PermissionError):
            AdminUsuarioService.eliminar_usuario_admin(
                otro_admin.id,
                self.admin,
                forzar=False
            )
    
    def test_eliminar_usuario_inexistente_falla(self):
        """Test: no se puede eliminar usuario que no existe"""
        with self.assertRaises(ValueError):
            AdminUsuarioService.eliminar_usuario_admin(
                999999,  # ID inexistente
                self.admin,
                forzar=False
            )


class AdminListarUsuariosTestCase(TestCase):
    """Tests para listar usuarios con filtros"""
    
    def setUp(self):
        """Crear usuarios de prueba"""
        # Crear categoría y servicio para profesionales
        categoria = Categoria.objects.create(
            nombre='Test',
            descripcion='Test'
        )
        servicio = Servicio.objects.create(
            nombre='Test',
            descripcion='Test',
            categoria=categoria,
            precio_base=50.00,
            duracion_estimada=120
        )
        
        # Crear clientes
        for i in range(5):
            usuario = Usuario.objects.create_user(
                username=f'cliente{i}',
                email=f'cliente{i}@test.com',
                password='Pass123!',
                first_name=f'Cliente{i}',
                last_name='Test'
            )
            Cliente.objects.create(usuario=usuario)
        
        # Crear profesionales
        for i in range(3):
            usuario = Usuario.objects.create_user(
                username=f'profesional{i}',
                email=f'profesional{i}@test.com',
                password='Pass123!',
                first_name=f'Profesional{i}',
                last_name='Test'
            )
            profesional = Profesional.objects.create(
                usuario=usuario,
                anios_experiencia=i+1
            )
            profesional.servicios.add(servicio)
        
        # Crear admin
        Usuario.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='Admin123!',
            is_staff=True,
            is_superuser=True
        )
    
    def test_listar_todos_usuarios(self):
        """Test: listar todos los usuarios"""
        filtros = {'pagina': 1, 'por_pagina': 20}
        resultado = AdminUsuarioService.listar_usuarios(filtros)
        
        # 5 clientes + 3 profesionales + 1 admin = 9 usuarios
        self.assertEqual(resultado['total'], 9)
        self.assertEqual(len(resultado['usuarios']), 9)
    
    def test_filtrar_por_rol_cliente(self):
        """Test: filtrar solo clientes"""
        filtros = {'rol': 'cliente', 'pagina': 1, 'por_pagina': 20}
        resultado = AdminUsuarioService.listar_usuarios(filtros)
        
        self.assertEqual(resultado['total'], 5)
    
    def test_filtrar_por_rol_profesional(self):
        """Test: filtrar solo profesionales"""
        filtros = {'rol': 'profesional', 'pagina': 1, 'por_pagina': 20}
        resultado = AdminUsuarioService.listar_usuarios(filtros)
        
        self.assertEqual(resultado['total'], 3)
    
    def test_buscar_por_nombre(self):
        """Test: buscar usuarios por nombre"""
        filtros = {'busqueda': 'Cliente0', 'pagina': 1, 'por_pagina': 20}
        resultado = AdminUsuarioService.listar_usuarios(filtros)
        
        self.assertGreaterEqual(resultado['total'], 1)
        self.assertTrue(
            any('Cliente0' in u.first_name for u in resultado['usuarios'])
        )
    
    def test_paginacion(self):
        """Test: verificar paginación"""
        # Primera página con 3 elementos
        filtros = {'pagina': 1, 'por_pagina': 3}
        resultado = AdminUsuarioService.listar_usuarios(filtros)
        
        self.assertEqual(len(resultado['usuarios']), 3)
        self.assertTrue(resultado['tiene_siguiente'])
        self.assertFalse(resultado['tiene_anterior'])
        
        # Segunda página
        filtros = {'pagina': 2, 'por_pagina': 3}
        resultado = AdminUsuarioService.listar_usuarios(filtros)
        
        self.assertTrue(resultado['tiene_anterior'])
    
    def test_ordenamiento_por_fecha(self):
        """Test: ordenar por fecha de registro"""
        filtros = {'orden': '-fecha_registro', 'pagina': 1, 'por_pagina': 20}
        resultado = AdminUsuarioService.listar_usuarios(filtros)
        
        # Verificar que están ordenados (más reciente primero)
        fechas = [u.date_joined for u in resultado['usuarios']]
        self.assertEqual(fechas, sorted(fechas, reverse=True))
