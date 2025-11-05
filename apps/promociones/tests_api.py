"""
Tests para la API de Promociones
Prueba todos los endpoints y reglas de negocio (CU-18, CU-19, CU-20)
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from decimal import Decimal

from apps.usuarios.models import Usuario
from apps.servicios.models import Categoria, Servicio
from apps.promociones.models import Promocion
from apps.promociones.services import PromocionService


class PromocionAPITestCase(TestCase):
    """Tests para los endpoints de la API de Promociones"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        
        # Crear usuario administrador
        self.usuario_admin = Usuario.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='Test',
            rol='administrador'
        )
        
        # Crear categoría y servicios de prueba
        self.categoria = Categoria.objects.create(
            nombre='Limpieza',
            descripcion='Servicios de limpieza'
        )
        
        self.servicio1 = Servicio.objects.create(
            nombre='Limpieza General',
            descripcion='Limpieza general del hogar',
            categoria=self.categoria,
            precio_base=Decimal('1000.00'),
            duracion_estimada=120
        )
        
        self.servicio2 = Servicio.objects.create(
            nombre='Limpieza Profunda',
            descripcion='Limpieza profunda del hogar',
            categoria=self.categoria,
            precio_base=Decimal('2000.00'),
            duracion_estimada=240
        )
        
        # Fechas de prueba
        self.fecha_inicio = timezone.now() + timedelta(days=1)
        self.fecha_fin = timezone.now() + timedelta(days=30)
        
        # Autenticar como administrador
        self.client.force_authenticate(user=self.usuario_admin)
    
    def test_registrar_promocion_exitoso(self):
        """CU-18: Test de registro exitoso de promoción"""
        data = {
            'titulo': 'Promoción de Prueba',
            'descripcion': 'Descripción de prueba',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '15.00',
            'categoria': self.categoria.id,
            'servicios': [self.servicio1.id, self.servicio2.id],
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'codigo': 'TEST2025'
        }
        
        response = self.client.post('/api/promociones/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['titulo'], 'Promoción de Prueba')
        self.assertTrue(response.data['data']['activa'])
        
        # Verificar que se creó en la BD
        self.assertTrue(Promocion.objects.filter(titulo='Promoción de Prueba').exists())
    
    def test_registrar_promocion_fechas_invalidas(self):
        """CU-18: Test de error por fechas incoherentes"""
        data = {
            'titulo': 'Promoción Test',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '10.00',
            'fecha_inicio': self.fecha_fin.isoformat(),  # Inicio después del fin
            'fecha_fin': self.fecha_inicio.isoformat(),
        }
        
        response = self.client.post('/api/promociones/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('fechas', response.data['errors'])
    
    def test_registrar_promocion_porcentaje_invalido(self):
        """CU-18: Test de error por porcentaje fuera de rango"""
        data = {
            'titulo': 'Promoción Test',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '150.00',  # Mayor a 100%
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
        }
        
        response = self.client.post('/api/promociones/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('valor_descuento', response.data['errors'])
    
    def test_registrar_promocion_nombre_duplicado(self):
        """CU-18: Test de error por nombre duplicado"""
        # Crear primera promoción
        Promocion.objects.create(
            titulo='Promoción Única',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        # Intentar crear otra con el mismo nombre
        data = {
            'titulo': 'Promoción Única',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '15.00',
            'fecha_inicio': (self.fecha_fin + timedelta(days=1)).isoformat(),
            'fecha_fin': (self.fecha_fin + timedelta(days=30)).isoformat(),
        }
        
        response = self.client.post('/api/promociones/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('titulo', response.data['errors'])
    
    def test_registrar_promocion_solapada(self):
        """CU-18: Test de error por promociones solapadas"""
        # Crear promoción existente
        Promocion.objects.create(
            titulo='Promo Existente',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            categoria=self.categoria,
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        # Intentar crear otra solapada en la misma categoría
        data = {
            'titulo': 'Nueva Promoción',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': '20.00',
            'categoria': self.categoria.id,
            'fecha_inicio': (self.fecha_inicio + timedelta(days=5)).isoformat(),
            'fecha_fin': (self.fecha_fin - timedelta(days=5)).isoformat(),
        }
        
        response = self.client.post('/api/promociones/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('solape', response.data['errors'])
    
    def test_listar_promociones(self):
        """Test de listado de promociones"""
        # Crear promociones de prueba
        Promocion.objects.create(
            titulo='Promo 1',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            activa=True
        )
        
        Promocion.objects.create(
            titulo='Promo 2',
            tipo_descuento='monto_fijo',
            valor_descuento=Decimal('500.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            activa=False
        )
        
        response = self.client.get('/api/promociones/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['data']), 2)
    
    def test_listar_promociones_filtro_activa(self):
        """Test de filtrado por estado activo"""
        Promocion.objects.create(
            titulo='Promo Activa',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            activa=True
        )
        
        Promocion.objects.create(
            titulo='Promo Inactiva',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            activa=False
        )
        
        response = self.client.get('/api/promociones/?activa=true')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['data'][0]['titulo'], 'Promo Activa')
    
    def test_obtener_detalle_promocion(self):
        """Test de obtención de detalle de promoción"""
        promocion = Promocion.objects.create(
            titulo='Promo Detalle',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        response = self.client.get(f'/api/promociones/{promocion.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['titulo'], 'Promo Detalle')
    
    def test_modificar_promocion_exitoso(self):
        """CU-19: Test de modificación exitosa de promoción"""
        promocion = Promocion.objects.create(
            titulo='Promo Original',
            descripcion='Descripción original',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        data = {
            'titulo': 'Promo Modificada',
            'valor_descuento': '20.00'
        }
        
        response = self.client.put(f'/api/promociones/{promocion.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['titulo'], 'Promo Modificada')
        self.assertEqual(response.data['data']['valor_descuento'], '20.00')
        
        # Verificar que se actualizó en la BD
        promocion.refresh_from_db()
        self.assertEqual(promocion.titulo, 'Promo Modificada')
    
    def test_modificar_promocion_nombre_duplicado(self):
        """CU-19: Test de error al modificar con nombre duplicado"""
        promo1 = Promocion.objects.create(
            titulo='Promo 1',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        promo2 = Promocion.objects.create(
            titulo='Promo 2',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        # Intentar cambiar el nombre de promo2 a 'Promo 1'
        data = {'titulo': 'Promo 1'}
        
        response = self.client.put(f'/api/promociones/{promo2.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('titulo', response.data['errors'])
    
    def test_eliminar_promocion_exitoso(self):
        """CU-20: Test de eliminación exitosa sin turnos activos"""
        promocion = Promocion.objects.create(
            titulo='Promo a Eliminar',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            activa=True
        )
        
        response = self.client.delete(f'/api/promociones/{promocion.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar que se marcó como inactiva (soft delete)
        promocion.refresh_from_db()
        self.assertFalse(promocion.activa)
    
    def test_validar_eliminacion_sin_turnos(self):
        """CU-20: Test de validación de eliminación sin turnos"""
        promocion = Promocion.objects.create(
            titulo='Promo Test',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        response = self.client.get(f'/api/promociones/{promocion.id}/validar-eliminacion/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['puede_eliminar'])
        self.assertEqual(response.data['turnos_activos'], 0)
    
    def test_listar_promociones_vigentes_publico(self):
        """Test de listado de promociones vigentes (endpoint público)"""
        # Crear promoción vigente
        Promocion.objects.create(
            titulo='Promo Vigente',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('15.00'),
            fecha_inicio=timezone.now() - timedelta(days=1),
            fecha_fin=timezone.now() + timedelta(days=30),
            activa=True
        )
        
        # Crear promoción no vigente (futura)
        Promocion.objects.create(
            titulo='Promo Futura',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('20.00'),
            fecha_inicio=timezone.now() + timedelta(days=60),
            fecha_fin=timezone.now() + timedelta(days=90),
            activa=True
        )
        
        # Sin autenticación
        client_publico = APIClient()
        response = client_publico.get('/api/promociones/vigentes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['data'][0]['titulo'], 'Promo Vigente')
    
    def test_sin_autenticacion(self):
        """Test de error al acceder sin autenticación"""
        client_sin_auth = APIClient()
        
        response = client_sin_auth.get('/api/promociones/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = client_sin_auth.post('/api/promociones/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PromocionServiceTestCase(TestCase):
    """Tests para el servicio de lógica de negocio de Promociones"""
    
    def setUp(self):
        """Configuración inicial"""
        self.fecha_inicio = timezone.now() + timedelta(days=1)
        self.fecha_fin = timezone.now() + timedelta(days=30)
    
    def test_validar_fechas_correctas(self):
        """Test de validación de fechas correctas"""
        valido, mensaje = PromocionService.validar_fechas(
            self.fecha_inicio,
            self.fecha_fin
        )
        
        self.assertTrue(valido)
        self.assertEqual(mensaje, "")
    
    def test_validar_fechas_incorrectas(self):
        """Test de validación de fechas incorrectas"""
        valido, mensaje = PromocionService.validar_fechas(
            self.fecha_fin,  # Inicio después del fin
            self.fecha_inicio
        )
        
        self.assertFalse(valido)
        self.assertIn("anterior", mensaje.lower())
    
    def test_validar_porcentaje_valido(self):
        """Test de validación de porcentaje válido"""
        valido, mensaje = PromocionService.validar_valor_descuento(
            'porcentaje',
            Decimal('50.00')
        )
        
        self.assertTrue(valido)
    
    def test_validar_porcentaje_mayor_100(self):
        """Test de error por porcentaje mayor a 100%"""
        valido, mensaje = PromocionService.validar_valor_descuento(
            'porcentaje',
            Decimal('150.00')
        )
        
        self.assertFalse(valido)
        self.assertIn('100', mensaje)
    
    def test_validar_monto_fijo_valido(self):
        """Test de validación de monto fijo válido"""
        valido, mensaje = PromocionService.validar_valor_descuento(
            'monto_fijo',
            Decimal('5000.00')
        )
        
        self.assertTrue(valido)
    
    def test_validar_nombre_unico_nuevo(self):
        """Test de validación de nombre único para nueva promoción"""
        valido, mensaje = PromocionService.validar_nombre_unico('Promoción Nueva')
        
        self.assertTrue(valido)
    
    def test_validar_nombre_duplicado(self):
        """Test de error por nombre duplicado"""
        Promocion.objects.create(
            titulo='Promo Existente',
            tipo_descuento='porcentaje',
            valor_descuento=Decimal('10.00'),
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin
        )
        
        valido, mensaje = PromocionService.validar_nombre_unico('Promo Existente')
        
        self.assertFalse(valido)
        self.assertIn('existe', mensaje.lower())
