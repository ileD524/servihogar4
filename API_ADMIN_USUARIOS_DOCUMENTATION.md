# Gestión Administrativa de Usuarios - ServiHogar

## Resumen Ejecutivo

Esta documentación describe la implementación completa de los casos de uso **CU-04 (Registrar Usuario por Admin)**, **CU-05 (Modificar Usuario por Admin)** y **CU-06 (Eliminar Usuario por Admin)** para el sistema ServiHogar.

La implementación sigue una arquitectura REST con separación en capas:
- **Capa de Servicios**: Lógica de negocio (`admin_services.py`)
- **Capa de API**: Endpoints REST (`admin_api_views.py`)
- **Capa de Serialización**: Validación de datos (`serializers.py`)
- **Capa de Pruebas**: Tests unitarios (`tests_admin_services.py`)

---

## 📋 Tabla de Contenidos

1. [Casos de Uso Implementados](#casos-de-uso-implementados)
2. [Arquitectura](#arquitectura)
3. [Endpoints API](#endpoints-api)
4. [Modelos de Datos](#modelos-de-datos)
5. [Seguridad y Permisos](#seguridad-y-permisos)
6. [Validaciones](#validaciones)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Testing](#testing)
9. [Logging y Auditoría](#logging-y-auditoría)

---

## Casos de Uso Implementados

### CU-04: Registrar Usuario (Administrador)

**Actor**: Administrador del sistema

**Descripción**: Permite al administrador crear nuevos usuarios (clientes o profesionales) con control completo sobre su configuración inicial.

**Capacidades especiales**:
- ✅ Crear usuarios directamente **activos** o en estado **pendiente**
- ✅ Asignar roles: cliente o profesional
- ✅ Configurar servicios para profesionales
- ✅ Crear con autenticación manual o Google OAuth
- ✅ Generar contraseña temporal si no se proporciona
- ✅ Enviar email de confirmación o bienvenida según el estado

**Archivo**: `apps/usuarios/admin_services.py` → `AdminUsuarioService.registrar_usuario_admin()`

---

### CU-05: Modificar Usuario (Administrador)

**Actor**: Administrador del sistema

**Descripción**: Permite al administrador modificar cualquier dato de usuarios existentes.

**Capacidades especiales**:
- ✅ Modificar datos básicos (nombre, email, teléfono, etc.)
- ✅ **Cambiar el rol** de cliente a profesional o viceversa
- ✅ **Activar/desactivar** usuarios
- ✅ Actualizar servicios y horarios de profesionales
- ✅ **Protección**: No puede modificar otros administradores
- ✅ Validaciones automáticas según el tipo de cambio

**Archivo**: `apps/usuarios/admin_services.py` → `AdminUsuarioService.modificar_usuario_admin()`

---

### CU-06: Eliminar Usuario (Administrador)

**Actor**: Administrador del sistema

**Descripción**: Permite al administrador eliminar usuarios del sistema con eliminación lógica.

**Capacidades especiales**:
- ✅ Validación automática: verifica que no haya turnos/pagos activos
- ✅ Opción de **forzar eliminación** (bypass de validaciones)
- ✅ **Eliminación lógica**: usuario queda inactivo
- ✅ **Anonimización de datos**: email y username modificados
- ✅ **Protección**: No puede eliminar otros administradores
- ✅ Envía notificación por email
- ✅ Auditoría completa de la operación

**Archivo**: `apps/usuarios/admin_services.py` → `AdminUsuarioService.eliminar_usuario_admin()`

---

## Arquitectura

### Estructura de Archivos

```
apps/usuarios/
├── admin_services.py         # Lógica de negocio administrativa
├── admin_api_views.py         # Endpoints REST administrativos
├── serializers.py             # Validación y serialización (ampliado)
├── api_urls.py                # Rutas API (ampliado)
├── tests_admin_services.py    # Tests para funcionalidad admin
├── validators.py              # Validadores reutilizables (existente)
├── emails.py                  # Sistema de emails (existente)
└── models.py                  # Modelos de datos (existente)
```

### Flujo de Solicitud

```
Cliente HTTP
    ↓
[admin_api_views.py] - Endpoint REST
    ↓
[serializers.py] - Validación de entrada
    ↓
[admin_services.py] - Lógica de negocio
    ↓
[validators.py] - Validaciones específicas
    ↓
[models.py] - Persistencia en BD
    ↓
[emails.py] - Notificaciones (opcional)
```

---

## Endpoints API

### Base URL

Todos los endpoints administrativos están bajo:
```
/api/usuarios/admin/
```

**Autenticación requerida**: Sí (debe ser administrador)

---

### 1. Listar Usuarios

**Endpoint**: `GET /api/usuarios/admin/`

**Descripción**: Lista todos los usuarios con opciones de filtrado, búsqueda y paginación.

**Query Parameters**:
| Parámetro | Tipo | Obligatorio | Descripción | Ejemplo |
|-----------|------|-------------|-------------|---------|
| `rol` | string | No | Filtrar por rol | `cliente`, `profesional`, `administrador` |
| `activo` | boolean | No | Filtrar por estado | `true`, `false` |
| `busqueda` | string | No | Buscar en nombre, email, username | `juan` |
| `orden` | string | No | Campo de ordenamiento | `username`, `-fecha_registro` |
| `pagina` | integer | No | Número de página (default: 1) | `2` |
| `por_pagina` | integer | No | Elementos por página (default: 20, max: 100) | `50` |

**Ejemplo de Request**:
```bash
GET /api/usuarios/admin/?rol=profesional&activo=true&pagina=1&por_pagina=20
```

**Ejemplo de Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "usuarios": [
      {
        "id": 5,
        "username": "profesional1",
        "email": "prof1@ejemplo.com",
        "first_name": "Carlos",
        "last_name": "López",
        "rol": "profesional",
        "activo": true,
        "fecha_registro": "2025-01-15T10:30:00Z",
        "ultimo_acceso": "2025-01-20T14:22:00Z",
        "profesional": {
          "anios_experiencia": 5,
          "calificacion_promedio": 4.8,
          "servicios": ["Limpieza", "Plomería"]
        }
      }
    ],
    "paginacion": {
      "total": 15,
      "pagina_actual": 1,
      "total_paginas": 1,
      "por_pagina": 20,
      "tiene_siguiente": false,
      "tiene_anterior": false
    },
    "filtros_aplicados": {
      "rol": "profesional",
      "activo": true,
      "busqueda": null,
      "orden": "-fecha_registro"
    }
  }
}
```

---

### 2. Obtener Detalle de Usuario

**Endpoint**: `GET /api/usuarios/admin/<id>/`

**Descripción**: Obtiene toda la información de un usuario específico.

**Parámetros URL**:
- `id`: ID del usuario

**Ejemplo de Request**:
```bash
GET /api/usuarios/admin/5/
```

**Ejemplo de Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 5,
    "username": "profesional1",
    "email": "prof1@ejemplo.com",
    "first_name": "Carlos",
    "last_name": "López",
    "telefono": "123456789",
    "direccion": "Calle Principal 123",
    "rol": "profesional",
    "activo": true,
    "email_confirmado": true,
    "fecha_registro": "2025-01-15T10:30:00Z",
    "ultimo_acceso": "2025-01-20T14:22:00Z",
    "google_id": null,
    "profesional": {
      "id": 3,
      "anios_experiencia": 5,
      "calificacion_promedio": 4.8,
      "servicios": [
        {
          "id": 1,
          "nombre": "Limpieza básica",
          "categoria": "Limpieza"
        }
      ],
      "horarios": [
        {
          "dia_semana": "lunes",
          "hora_inicio": "09:00:00",
          "hora_fin": "18:00:00",
          "activo": true
        }
      ]
    }
  }
}
```

---

### 3. Registrar Usuario (CU-04)

**Endpoint**: `POST /api/usuarios/admin/registrar/`

**Descripción**: Crea un nuevo usuario (cliente o profesional).

**Body Parameters**:
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `username` | string | Sí | Nombre de usuario único |
| `email` | string | Sí | Email único |
| `password` | string | No | Contraseña (se genera temporal si se omite) |
| `first_name` | string | Sí | Nombre |
| `last_name` | string | Sí | Apellido |
| `telefono` | string | No | Teléfono de contacto |
| `direccion` | string | No | Dirección |
| `rol` | string | Sí | `cliente` o `profesional` |
| `estado` | string | No | `activo` o `pendiente` (default: activo) |
| `google_id` | string | No | ID de Google OAuth |
| `anios_experiencia` | integer | No* | Años de experiencia (profesionales) |
| `servicios` | array[int] | No* | IDs de servicios (profesionales, obligatorio) |
| `horarios` | array[object] | No | Horarios disponibles (profesionales) |

\* Obligatorio para profesionales

**Ejemplo de Request** (Registrar Cliente):
```json
{
  "username": "nuevo_cliente",
  "email": "cliente@ejemplo.com",
  "password": "Cliente123!",
  "first_name": "María",
  "last_name": "García",
  "telefono": "987654321",
  "direccion": "Av. Libertador 456",
  "rol": "cliente",
  "estado": "activo"
}
```

**Ejemplo de Request** (Registrar Profesional):
```json
{
  "username": "nuevo_profesional",
  "email": "prof@ejemplo.com",
  "password": "Prof123!",
  "first_name": "Juan",
  "last_name": "Pérez",
  "telefono": "123456789",
  "rol": "profesional",
  "estado": "activo",
  "anios_experiencia": 8,
  "servicios": [1, 2, 3],
  "horarios": [
    {
      "dia": "lunes",
      "hora_inicio": "09:00",
      "hora_fin": "18:00"
    },
    {
      "dia": "martes",
      "hora_inicio": "10:00",
      "hora_fin": "19:00"
    }
  ]
}
```

**Ejemplo de Response** (201 Created):
```json
{
  "success": true,
  "message": "Usuario registrado exitosamente",
  "data": {
    "usuario_id": 10,
    "username": "nuevo_profesional",
    "email": "prof@ejemplo.com",
    "rol": "profesional",
    "estado": "activo",
    "requiere_confirmacion": false
  }
}
```

**Errores Comunes**:
```json
// 400 Bad Request - Email duplicado
{
  "success": false,
  "error": "El email ya está registrado"
}

// 400 Bad Request - Profesional sin servicios
{
  "success": false,
  "errors": {
    "servicios": ["Los profesionales deben tener al menos un servicio asignado"]
  }
}
```

---

### 4. Modificar Usuario (CU-05)

**Endpoint**: `PUT /api/usuarios/admin/<id>/modificar/` o `PATCH /api/usuarios/admin/<id>/modificar/`

**Descripción**: Modifica los datos de un usuario existente.

**Parámetros URL**:
- `id`: ID del usuario a modificar

**Body Parameters** (todos opcionales):
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `username` | string | Nuevo nombre de usuario |
| `email` | string | Nuevo email |
| `first_name` | string | Nuevo nombre |
| `last_name` | string | Nuevo apellido |
| `telefono` | string | Nuevo teléfono |
| `direccion` | string | Nueva dirección |
| `rol` | string | Cambiar rol (`cliente` o `profesional`) |
| `activo` | boolean | Activar/desactivar usuario |
| `anios_experiencia` | integer | Actualizar experiencia (profesionales) |
| `servicios` | array[int] | Actualizar servicios (profesionales) |
| `horarios` | array[object] | Actualizar horarios (profesionales) |

**Ejemplo de Request** (Cambiar datos básicos):
```json
{
  "first_name": "Carlos Actualizado",
  "telefono": "555666777",
  "direccion": "Nueva dirección 789"
}
```

**Ejemplo de Request** (Desactivar usuario):
```json
{
  "activo": false
}
```

**Ejemplo de Request** (Cambiar de cliente a profesional):
```json
{
  "rol": "profesional",
  "servicios": [1, 2],
  "anios_experiencia": 3,
  "horarios": [
    {
      "dia": "lunes",
      "hora_inicio": "08:00",
      "hora_fin": "17:00"
    }
  ]
}
```

**Ejemplo de Response** (200 OK):
```json
{
  "success": true,
  "message": "Usuario modificado exitosamente",
  "data": {
    "usuario_id": 5,
    "username": "profesional1",
    "email": "prof1@ejemplo.com",
    "rol": "profesional",
    "activo": true,
    "cambios_realizados": ["first_name", "telefono", "direccion"]
  }
}
```

**Errores Comunes**:
```json
// 403 Forbidden - Intento de modificar otro admin
{
  "success": false,
  "error": "No se puede modificar a otros administradores"
}

// 400 Bad Request - Cambio de rol con turnos activos
{
  "success": false,
  "error": "No se puede cambiar el rol del usuario porque tiene turnos activos"
}
```

---

### 5. Eliminar Usuario (CU-06)

**Endpoint**: `DELETE /api/usuarios/admin/<id>/eliminar/`

**Descripción**: Elimina un usuario del sistema (eliminación lógica con anonimización).

**Parámetros URL**:
- `id`: ID del usuario a eliminar

**Body Parameters**:
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `confirmar` | boolean | Sí | Debe ser `true` para confirmar |
| `forzar` | boolean | No | `true` para forzar eliminación (default: false) |

**Ejemplo de Request** (Eliminación normal):
```json
{
  "confirmar": true,
  "forzar": false
}
```

**Ejemplo de Request** (Forzar eliminación):
```json
{
  "confirmar": true,
  "forzar": true
}
```

**Ejemplo de Response** (200 OK):
```json
{
  "success": true,
  "message": "Usuario eliminado exitosamente",
  "data": {
    "usuario_id": 5,
    "username_anonimizado": "eliminado_5_20250120",
    "forzado": false
  }
}
```

**Errores Comunes**:
```json
// 403 Forbidden - Intento de eliminar otro admin
{
  "success": false,
  "error": "No se puede eliminar a otros administradores"
}

// 400 Bad Request - Usuario con turnos activos (sin forzar)
{
  "success": false,
  "error": "El usuario tiene turnos activos y no puede ser eliminado. Use la opción 'forzar' si es necesario."
}

// 400 Bad Request - No confirmó
{
  "success": false,
  "errors": {
    "confirmar": ["Debe confirmar explícitamente que desea eliminar este usuario"]
  }
}
```

---

## Modelos de Datos

### Usuario (Django User Model extendido)

```python
class Usuario(AbstractUser):
    """Modelo de usuario extendido"""
    
    # Campos básicos heredados de AbstractUser:
    # - username
    # - email
    # - first_name
    # - last_name
    # - password
    # - is_active
    # - is_staff
    # - is_superuser
    # - date_joined
    # - last_login
    
    # Campos adicionales
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    email_confirmado = models.BooleanField(default=False)
    token_confirmacion = models.CharField(max_length=100, blank=True)
    token_expiracion = models.DateTimeField(null=True, blank=True)
    google_id = models.CharField(max_length=255, blank=True, unique=True)
    foto_perfil = models.ImageField(upload_to='usuarios/', blank=True)
```

### Cliente

```python
class Cliente(models.Model):
    """Perfil de cliente"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    preferencias = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
```

### Profesional

```python
class Profesional(models.Model):
    """Perfil de profesional"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    anios_experiencia = models.IntegerField(default=0)
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    servicios = models.ManyToManyField('servicios.Servicio')
    fecha_registro = models.DateTimeField(auto_now_add=True)
```

---

## Seguridad y Permisos

### Autenticación

Todos los endpoints administrativos requieren:
1. **Usuario autenticado** (sesión activa)
2. **Permisos de administrador** (`is_staff=True` y `is_superuser=True`)

```python
@permission_classes([IsAdminUser])
```

### Protecciones Implementadas

#### 1. Protección entre Administradores

```python
# Un admin NO puede modificar/eliminar a otro admin
if usuario_objetivo.is_staff and usuario_objetivo.is_superuser:
    raise PermissionError("No se puede modificar/eliminar a otros administradores")
```

#### 2. Validación de Email Único

```python
if Usuario.objects.filter(email=nuevo_email).exclude(id=usuario_id).exists():
    raise ValueError("El email ya está en uso")
```

#### 3. Validación de Username Único

```python
if Usuario.objects.filter(username=nuevo_username).exclude(id=usuario_id).exists():
    raise ValueError("El nombre de usuario ya está en uso")
```

#### 4. Eliminación Lógica (No Física)

```python
# NO se elimina el registro de la base de datos
usuario.is_active = False
usuario.email = f"eliminado_{usuario.id}_{timezone.now().strftime('%Y%m%d')}"
usuario.username = f"eliminado_{usuario.id}"
usuario.save()
```

#### 5. Validación de Cambio de Rol

```python
# No se puede cambiar rol si hay turnos activos
if Turno.objects.filter(
    Q(cliente__usuario=usuario) | Q(profesional__usuario=usuario),
    estado__in=['pendiente', 'confirmado']
).exists():
    raise ValueError("No se puede cambiar el rol con turnos activos")
```

---

## Validaciones

### Validaciones en `UsuarioValidator`

```python
class UsuarioValidator:
    @staticmethod
    def validar_email_formato(email):
        """Valida formato de email"""
        
    @staticmethod
    def validar_email_unico(email, usuario_id=None):
        """Valida que el email no esté en uso"""
        
    @staticmethod
    def validar_contrasena_segura(password):
        """Valida complejidad de contraseña"""
        # - Al menos 8 caracteres
        # - Al menos una mayúscula
        # - Al menos una minúscula
        # - Al menos un número
        
    @staticmethod
    def validar_telefono(telefono):
        """Valida formato de teléfono"""
        
    @staticmethod
    def validar_horarios(horarios):
        """Valida formato de horarios para profesionales"""
```

### Validaciones en Serializers

#### AdminRegistroUsuarioSerializer

- `username`: Máx. 150 caracteres, único
- `email`: Formato válido, único
- `password`: Opcional (se genera si no se proporciona)
- `rol`: Solo 'cliente' o 'profesional'
- `estado`: Solo 'activo' o 'pendiente'
- `servicios`: Requerido si rol='profesional', mínimo 1

#### AdminModificarUsuarioSerializer

- Todos los campos opcionales
- `email`: Único (excepto para el usuario actual)
- `username`: Único (excepto para el usuario actual)
- `rol`: Validación de cambio con verificación de turnos activos
- `servicios`: Si cambia a profesional, mínimo 1

#### AdminEliminarUsuarioSerializer

- `confirmar`: Debe ser `true`
- `forzar`: Booleano opcional

---

## Ejemplos de Uso

### Ejemplo 1: Crear un Cliente Activo

```bash
curl -X POST http://localhost:8000/api/usuarios/admin/registrar/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "maria_garcia",
    "email": "maria@ejemplo.com",
    "password": "MiPassword123!",
    "first_name": "María",
    "last_name": "García",
    "telefono": "555123456",
    "direccion": "Calle 123",
    "rol": "cliente",
    "estado": "activo"
  }'
```

### Ejemplo 2: Crear un Profesional con Servicios

```bash
curl -X POST http://localhost:8000/api/usuarios/admin/registrar/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan_plomero",
    "email": "juan@ejemplo.com",
    "password": "Plomero123!",
    "first_name": "Juan",
    "last_name": "Pérez",
    "telefono": "555987654",
    "rol": "profesional",
    "estado": "activo",
    "anios_experiencia": 10,
    "servicios": [1, 2],
    "horarios": [
      {
        "dia": "lunes",
        "hora_inicio": "08:00",
        "hora_fin": "17:00"
      },
      {
        "dia": "martes",
        "hora_inicio": "08:00",
        "hora_fin": "17:00"
      }
    ]
  }'
```

### Ejemplo 3: Buscar Profesionales Activos

```bash
curl -X GET "http://localhost:8000/api/usuarios/admin/?rol=profesional&activo=true&orden=-fecha_registro" \
  -H "Authorization: Bearer <token_admin>"
```

### Ejemplo 4: Cambiar el Rol de un Usuario

```bash
curl -X PUT http://localhost:8000/api/usuarios/admin/15/modificar/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "rol": "profesional",
    "servicios": [3, 4],
    "anios_experiencia": 5
  }'
```

### Ejemplo 5: Desactivar un Usuario

```bash
curl -X PUT http://localhost:8000/api/usuarios/admin/20/modificar/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "activo": false
  }'
```

### Ejemplo 6: Eliminar un Usuario (con validaciones)

```bash
curl -X DELETE http://localhost:8000/api/usuarios/admin/25/eliminar/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "confirmar": true,
    "forzar": false
  }'
```

### Ejemplo 7: Forzar Eliminación

```bash
curl -X DELETE http://localhost:8000/api/usuarios/admin/30/eliminar/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "confirmar": true,
    "forzar": true
  }'
```

---

## Testing

### Tests Implementados

Se han implementado **28 tests unitarios** que cubren todos los casos de uso:

#### Tests para CU-04 (Registrar Usuario)

```python
class AdminRegistroUsuarioTestCase(TestCase):
    def test_registrar_cliente_activo(self):
        """Crear cliente directamente activo"""
        
    def test_registrar_cliente_pendiente(self):
        """Crear cliente en estado pendiente"""
        
    def test_registrar_profesional_con_servicios(self):
        """Crear profesional con servicios asignados"""
        
    def test_registrar_profesional_sin_servicios_falla(self):
        """Validar que profesional requiere servicios"""
        
    def test_registrar_sin_password_genera_temporal(self):
        """Generar password temporal automáticamente"""
        
    def test_registrar_email_duplicado_falla(self):
        """Validar unicidad de email"""
```

#### Tests para CU-05 (Modificar Usuario)

```python
class AdminModificarUsuarioTestCase(TestCase):
    def test_modificar_datos_basicos(self):
        """Modificar nombre, teléfono, dirección"""
        
    def test_activar_desactivar_usuario(self):
        """Cambiar estado activo/inactivo"""
        
    def test_cambiar_rol_cliente_a_profesional(self):
        """Cambio de rol con actualización de perfil"""
        
    def test_no_puede_modificar_otro_admin(self):
        """Protección entre administradores"""
        
    def test_modificar_usuario_inexistente_falla(self):
        """Manejo de usuario no encontrado"""
```

#### Tests para CU-06 (Eliminar Usuario)

```python
class AdminEliminarUsuarioTestCase(TestCase):
    def test_eliminar_usuario_sin_turnos(self):
        """Eliminación lógica con anonimización"""
        
    def test_eliminar_con_forzar(self):
        """Forzar eliminación con flag"""
        
    def test_no_puede_eliminar_otro_admin(self):
        """Protección entre administradores"""
        
    def test_eliminar_usuario_inexistente_falla(self):
        """Manejo de usuario no encontrado"""
```

#### Tests para Listado y Filtros

```python
class AdminListarUsuariosTestCase(TestCase):
    def test_listar_todos_usuarios(self):
        """Listar sin filtros"""
        
    def test_filtrar_por_rol_cliente(self):
        """Filtrar solo clientes"""
        
    def test_filtrar_por_rol_profesional(self):
        """Filtrar solo profesionales"""
        
    def test_buscar_por_nombre(self):
        """Búsqueda por texto"""
        
    def test_paginacion(self):
        """Verificar paginación correcta"""
        
    def test_ordenamiento_por_fecha(self):
        """Ordenamiento por campos"""
```

### Ejecutar Tests

```bash
# Todos los tests de usuarios
python manage.py test apps.usuarios

# Solo tests administrativos
python manage.py test apps.usuarios.tests_admin_services

# Con verbose
python manage.py test apps.usuarios.tests_admin_services --verbosity=2

# Con coverage
coverage run --source='apps.usuarios' manage.py test apps.usuarios.tests_admin_services
coverage report
```

---

## Logging y Auditoría

### Logs Implementados

Todos los servicios administrativos registran las operaciones en el log del sistema:

```python
import logging
logger = logging.getLogger(__name__)

# Registro exitoso
logger.info(f"Usuario {usuario.username} registrado por admin {admin_usuario.username}")

# Modificación
logger.info(f"Usuario {usuario.username} modificado por admin {admin_usuario.username}. Cambios: {', '.join(datos_actualizados.keys())}")

# Eliminación
logger.info(f"Usuario {usuario.username} (ID: {usuario.id}) eliminado por admin {admin_usuario.username}")

# Advertencias
logger.warning(f"Error de validación al registrar usuario (admin): {str(e)}")

# Errores
logger.error(f"Error inesperado al modificar usuario (admin): {str(e)}")
```

### Configuración de Logging

En `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/admin_operations.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.usuarios.admin_services': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Auditoría de Operaciones

Cada operación administrativa queda registrada con:
- **Timestamp**: Fecha y hora exacta
- **Admin**: Usuario administrador que realizó la acción
- **Usuario afectado**: ID y username
- **Operación**: Tipo de acción (registro, modificación, eliminación)
- **Detalles**: Campos modificados o motivo de error

**Ejemplo de log**:
```
[2025-01-20 15:30:22] INFO - Usuario juan_perez registrado por admin admin_principal
[2025-01-20 15:32:10] INFO - Usuario maria_garcia modificado por admin admin_principal. Cambios: first_name, telefono, activo
[2025-01-20 15:35:45] INFO - Usuario carlos_lopez (ID: 25) eliminado por admin admin_principal
```

---

## Mejores Prácticas

### 1. Separación de Responsabilidades

- **admin_services.py**: Solo lógica de negocio
- **admin_api_views.py**: Solo manejo de HTTP requests/responses
- **serializers.py**: Solo validación y serialización
- **validators.py**: Validadores reutilizables

### 2. Manejo de Errores

```python
try:
    resultado = AdminUsuarioService.registrar_usuario_admin(datos, admin)
    return Response({'success': True, 'data': resultado}, status=201)
except ValueError as e:
    return Response({'success': False, 'error': str(e)}, status=400)
except PermissionError as e:
    return Response({'success': False, 'error': str(e)}, status=403)
except Exception as e:
    logger.error(f"Error inesperado: {str(e)}")
    return Response({'success': False, 'error': 'Error interno'}, status=500)
```

### 3. Validación en Capas

1. **Serializer**: Validación de formato y tipos
2. **Validator**: Validaciones de negocio reutilizables
3. **Service**: Validaciones contextuales

### 4. Documentación en Código

Todos los métodos y endpoints están documentados con:
- Descripción clara
- Parámetros esperados
- Tipos de retorno
- Excepciones posibles
- Ejemplos de uso

### 5. Testing Exhaustivo

- Test por cada caso de uso
- Test de casos límite
- Test de validaciones
- Test de permisos
- Test de errores

---

## Diferencias con la Gestión de Usuarios Regular

| Característica | Usuario Regular (CU-01, CU-02, CU-03) | Administrador (CU-04, CU-05, CU-06) |
|----------------|---------------------------------------|-------------------------------------|
| **Alcance** | Solo su propio perfil | Cualquier usuario (excepto otros admins) |
| **Estado inicial** | Siempre pendiente (requiere confirmación) | Puede ser activo o pendiente |
| **Cambio de rol** | No permitido | Permitido (con validaciones) |
| **Activar/Desactivar** | No permitido | Permitido |
| **Forzar eliminación** | No disponible | Disponible con flag `forzar` |
| **Password temporal** | No disponible | Se genera automáticamente si no se proporciona |
| **Endpoints** | `/api/usuarios/perfil/` | `/api/usuarios/admin/` |
| **Permisos** | Usuario autenticado | Solo administradores |

---

## Próximos Pasos

1. ✅ Implementar CU-04, CU-05, CU-06 (COMPLETADO)
2. ⏳ Integrar con frontend administrativo
3. ⏳ Implementar panel de administración visual
4. ⏳ Agregar exportación de datos (CSV, Excel)
5. ⏳ Implementar notificaciones push para admins
6. ⏳ Agregar filtros avanzados y gráficos

---

## Soporte

Para más información:
- Ver `API_USUARIOS_DOCUMENTATION.md` para documentación de API de usuarios regulares
- Ver `IMPLEMENTACION_USUARIOS.md` para detalles técnicos de implementación
- Ver `README_IMPLEMENTACION.md` para resumen ejecutivo del proyecto

---

## Resumen de Archivos Creados

1. **apps/usuarios/admin_services.py** (~650 líneas)
   - AdminUsuarioService con 4 métodos estáticos

2. **apps/usuarios/admin_api_views.py** (~600 líneas)
   - 5 endpoints REST para administradores

3. **apps/usuarios/serializers.py** (ampliado +~200 líneas)
   - 4 nuevos serializers para operaciones administrativas

4. **apps/usuarios/api_urls.py** (ampliado +~30 líneas)
   - 5 nuevas rutas administrativas

5. **apps/usuarios/tests_admin_services.py** (~450 líneas)
   - 28 tests unitarios

6. **API_ADMIN_USUARIOS_DOCUMENTATION.md** (este archivo, ~1000 líneas)
   - Documentación completa de funcionalidad administrativa

---

**Fecha de creación**: 2025-01-20  
**Versión**: 1.0.0  
**Autor**: Equipo ServiHogar
