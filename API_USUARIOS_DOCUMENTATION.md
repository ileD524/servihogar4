# Documentación API REST - Gestión de Perfiles de Usuario

## ServiHogar - Sistema de Reservas de Servicios

Esta documentación describe los endpoints REST para la gestión de perfiles de usuario, implementando los casos de uso CU-01 (Registrar Perfil), CU-02 (Eliminar Perfil) y CU-03 (Modificar Perfil).

---

## Tabla de Contenidos

1. [CU-01: Registrar Perfil](#cu-01-registrar-perfil)
2. [CU-02: Eliminar Perfil](#cu-02-eliminar-perfil)
3. [CU-03: Modificar Perfil](#cu-03-modificar-perfil)
4. [Arquitectura](#arquitectura)
5. [Ejemplos de Uso](#ejemplos-de-uso)

---

## CU-01: Registrar Perfil

Permite a un usuario no registrado crear un perfil como Cliente o Profesional.

### 1.1 Registro Manual

**Endpoint:** `POST /api/usuarios/registrar/`

**Autenticación:** No requerida

**Body (JSON):**
```json
{
  "username": "juanperez",
  "email": "juan.perez@example.com",
  "password": "Contraseña123!",
  "password_confirm": "Contraseña123!",
  "first_name": "Juan",
  "last_name": "Pérez",
  "telefono": "+54 11 1234-5678",
  "direccion": "Av. Ejemplo 123, CABA",
  "rol": "cliente"
}
```

Para **profesionales**, agregar campos adicionales:
```json
{
  "username": "mariagomez",
  "email": "maria.gomez@example.com",
  "password": "Contraseña456!",
  "password_confirm": "Contraseña456!",
  "first_name": "María",
  "last_name": "Gómez",
  "telefono": "+54 11 9876-5432",
  "direccion": "Calle Principal 456, CABA",
  "rol": "profesional",
  "anios_experiencia": 5,
  "servicios": [1, 3, 5],
  "horarios": [
    {
      "dia": "lunes",
      "hora_inicio": "09:00",
      "hora_fin": "18:00"
    },
    {
      "dia": "martes",
      "hora_inicio": "09:00",
      "hora_fin": "18:00"
    },
    {
      "dia": "miercoles",
      "hora_inicio": "14:00",
      "hora_fin": "20:00"
    }
  ]
}
```

**Validaciones:**
- Email: formato válido y único
- Contraseña: 
  - Mínimo 8 caracteres
  - Al menos una mayúscula
  - Al menos una minúscula
  - Al menos un número
- Teléfono: formato válido (7-20 dígitos)
- Profesionales: deben proporcionar servicios y horarios

**Respuesta exitosa (201 CREATED):**
```json
{
  "success": true,
  "message": "Usuario registrado exitosamente. Por favor revisa tu email para confirmar tu cuenta.",
  "usuario": {
    "id": 123,
    "username": "juanperez",
    "email": "juan.perez@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "nombre_completo": "Juan Pérez",
    "rol": "cliente",
    "rol_display": "Cliente",
    "telefono": "+54 11 1234-5678",
    "direccion": "Av. Ejemplo 123, CABA",
    "activo": false,
    "fecha_registro": "2025-11-05T10:30:00Z"
  }
}
```

**Respuesta con errores (400 BAD REQUEST):**
```json
{
  "success": false,
  "errors": {
    "email": ["Ya existe un usuario registrado con este email"],
    "password": ["La contraseña debe contener al menos una letra mayúscula"]
  }
}
```

---

### 1.2 Confirmar Email

**Endpoint:** `GET /api/usuarios/confirmar/<uidb64>/<token>/`

**Autenticación:** No requerida

**Descripción:** El usuario recibe un email con un enlace de confirmación. Al hacer clic, se activa la cuenta.

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "message": "¡Email confirmado exitosamente! Ya puedes iniciar sesión.",
  "usuario": {
    "id": 123,
    "activo": true,
    "is_active": true
  }
}
```

**Estado del usuario:**
- Antes de confirmar: `activo: false`, `is_active: false` (no puede iniciar sesión)
- Después de confirmar: `activo: true`, `is_active: true` (puede iniciar sesión)

---

### 1.3 Registro con Google OAuth

**Endpoint:** `POST /api/usuarios/registrar/google/`

**Autenticación:** No requerida

**Body (JSON):**
```json
{
  "code": "código_de_autorización_google",
  "google_id": "1234567890",
  "email": "usuario@gmail.com",
  "first_name": "Usuario",
  "last_name": "Google"
}
```

**Respuesta exitosa (201 CREATED):**
```json
{
  "success": true,
  "message": "Autenticación con Google exitosa",
  "usuario": {
    "id": 124,
    "username": "usuario",
    "email": "usuario@gmail.com",
    "first_name": "Usuario",
    "last_name": "Google",
    "rol": "cliente",
    "activo": true,
    "google_id": "1234567890"
  },
  "datos_completos": false
}
```

**Nota:** Los usuarios registrados con Google están activos inmediatamente y no necesitan confirmar email.

---

### 1.4 Completar Datos (Usuario Google)

**Endpoint:** `PUT /api/usuarios/completar-datos/`

**Autenticación:** Requerida (usuario autenticado con Google)

**Body (JSON):**
```json
{
  "telefono": "+54 11 5555-5555",
  "direccion": "Nueva Dirección 789",
  "rol": "profesional",
  "anios_experiencia": 3,
  "servicios": [2, 4],
  "horarios": [
    {
      "dia": "lunes",
      "hora_inicio": "10:00",
      "hora_fin": "17:00"
    }
  ]
}
```

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "message": "Datos completados exitosamente",
  "usuario": {
    "id": 124,
    "telefono": "+54 11 5555-5555",
    "direccion": "Nueva Dirección 789",
    "rol": "profesional",
    "perfil_profesional": {
      "anios_experiencia": 3,
      "servicios": [...],
      "horarios": [...]
    }
  }
}
```

---

## CU-02: Eliminar Perfil

Permite que un cliente/profesional elimine permanentemente su perfil.

### 2.1 Verificar si puede eliminar

**Endpoint:** `GET /api/usuarios/perfil/puede-eliminar/`

**Autenticación:** Requerida

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "puede_eliminar": true,
  "mensaje": "Puede eliminar su perfil"
}
```

**Si no puede eliminar:**
```json
{
  "success": true,
  "puede_eliminar": false,
  "mensaje": "No puede eliminar su perfil porque tiene turnos activos o pendientes"
}
```

---

### 2.2 Eliminar Perfil

**Endpoint:** `POST /api/usuarios/perfil/eliminar/`

**Autenticación:** Requerida

**Validaciones:**
- No tener turnos en estado: pendiente, confirmado o en_curso
- No tener pagos pendientes
- Confirmar explícitamente la eliminación

**Body (JSON) - Usuario con contraseña:**
```json
{
  "confirmar": true,
  "password": "Contraseña123!"
}
```

**Body (JSON) - Usuario con Google:**
```json
{
  "confirmar": true
}
```

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "message": "Perfil eliminado exitosamente",
  "fecha_eliminacion": "2025-11-05T15:45:00Z"
}
```

**Respuesta con error (400 BAD REQUEST):**
```json
{
  "success": false,
  "errors": ["No puede eliminar su perfil porque tiene turnos activos o pendientes"]
}
```

**Efectos de la eliminación:**
- Estado: `activo: false`, `is_active: false`
- Datos anonimizados:
  - `first_name`: "Usuario"
  - `last_name`: "Eliminado"
  - `email`: "eliminado_{id}@servihogar.local"
  - `username`: "eliminado_{id}"
  - `telefono`: ""
  - `direccion`: ""
- Foto de perfil: eliminada
- Perfil profesional: desasociado de servicios, horarios eliminados
- Se envía email de confirmación de baja
- ID y fecha de eliminación: mantenidos para auditoría

---

## CU-03: Modificar Perfil

Permite que un cliente/profesional autenticado modifique sus datos.

### 3.1 Obtener Perfil Actual

**Endpoint:** `GET /api/usuarios/perfil/`

**Autenticación:** Requerida

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "usuario": {
    "id": 123,
    "username": "juanperez",
    "email": "juan.perez@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "nombre_completo": "Juan Pérez",
    "rol": "cliente",
    "rol_display": "Cliente",
    "telefono": "+54 11 1234-5678",
    "direccion": "Av. Ejemplo 123, CABA",
    "foto_perfil": "/media/usuarios/juan_foto.jpg",
    "activo": true,
    "fecha_registro": "2025-11-05T10:30:00Z",
    "fecha_modificacion": "2025-11-05T12:15:00Z",
    "perfil_cliente": {
      "preferencias": "",
      "historial_busquedas": ""
    }
  }
}
```

---

### 3.2 Modificar Perfil

**Endpoint:** `PUT /api/usuarios/perfil/modificar/` o `PATCH /api/usuarios/perfil/modificar/`

**Autenticación:** Requerida

**Body (JSON) - Actualización parcial:**
```json
{
  "first_name": "Juan Carlos",
  "telefono": "+54 11 9999-9999",
  "direccion": "Nueva Dirección 321"
}
```

**Body (JSON) - Profesional actualizando servicios y horarios:**
```json
{
  "email": "nuevo.email@example.com",
  "telefono": "+54 11 8888-8888",
  "anios_experiencia": 7,
  "servicios": [1, 2, 3, 6],
  "horarios": [
    {
      "dia": "lunes",
      "hora_inicio": "08:00",
      "hora_fin": "16:00"
    },
    {
      "dia": "miercoles",
      "hora_inicio": "10:00",
      "hora_fin": "19:00"
    },
    {
      "dia": "viernes",
      "hora_inicio": "09:00",
      "hora_fin": "17:00"
    }
  ]
}
```

**Validaciones:**
- Email: si se cambia, debe ser único y formato válido
- Teléfono: formato válido
- Para profesionales: horarios deben tener formato correcto (hora_inicio < hora_fin)

**Respuesta exitosa (200 OK):**
```json
{
  "success": true,
  "message": "Perfil modificado exitosamente",
  "usuario": {
    "id": 123,
    "email": "nuevo.email@example.com",
    "telefono": "+54 11 8888-8888",
    "fecha_modificacion": "2025-11-05T16:20:00Z",
    "perfil_profesional": {
      "anios_experiencia": 7,
      "servicios": [...],
      "horarios": [...]
    }
  }
}
```

**Respuesta con errores (400 BAD REQUEST):**
```json
{
  "success": false,
  "errors": {
    "email": ["Este email ya está en uso"],
    "horarios": ["La hora de inicio debe ser menor que la hora de fin para lunes"]
  }
}
```

**Efectos de la modificación:**
- `fecha_modificacion`: actualizada automáticamente
- Email de notificación: enviado al usuario
- Para profesionales:
  - Servicios anteriores: desasociados
  - Nuevos servicios: asociados al profesional
  - Horarios antiguos: eliminados
  - Nuevos horarios: creados

---

## Arquitectura

### Estructura de Capas

```
┌─────────────────────────────────────────┐
│         API Views (api_views.py)        │  ← Endpoints REST
├─────────────────────────────────────────┤
│      Serializers (serializers.py)       │  ← Validación de entrada/salida
├─────────────────────────────────────────┤
│         Services (services.py)          │  ← Lógica de negocio
├─────────────────────────────────────────┤
│       Validators (validators.py)        │  ← Validaciones específicas
├─────────────────────────────────────────┤
│           Emails (emails.py)            │  ← Gestión de emails
├─────────────────────────────────────────┤
│          Models (models.py)             │  ← Persistencia de datos
└─────────────────────────────────────────┘
```

### Componentes Principales

#### 1. **api_views.py**
- Define endpoints REST
- Maneja autenticación y permisos
- Delega lógica a servicios
- Retorna respuestas JSON estandarizadas

#### 2. **serializers.py**
- Convierte objetos Python ↔ JSON
- Validaciones de entrada
- Campos requeridos/opcionales
- Mensajes de error personalizados

#### 3. **services.py**
- Lógica de negocio centralizada
- Transacciones atómicas
- Manejo de errores
- Separación de responsabilidades

#### 4. **validators.py**
- Validaciones reutilizables
- Reglas de negocio
- Independientes de vistas/modelos
- Mensajes de error en español

#### 5. **emails.py**
- Envío de emails
- Templates de mensajes
- Manejo de errores de envío
- Logging de operaciones

---

## Ejemplos de Uso

### Ejemplo 1: Registrar Cliente con Python requests

```python
import requests

url = "http://localhost:8000/api/usuarios/registrar/"

data = {
    "username": "cliente123",
    "email": "cliente@example.com",
    "password": "MiContraseña123!",
    "password_confirm": "MiContraseña123!",
    "first_name": "Cliente",
    "last_name": "Nuevo",
    "telefono": "+54 11 1234-5678",
    "rol": "cliente"
}

response = requests.post(url, json=data)

if response.status_code == 201:
    print("Usuario registrado exitosamente")
    print(response.json())
else:
    print("Error:", response.json())
```

### Ejemplo 2: Registrar Profesional con curl

```bash
curl -X POST http://localhost:8000/api/usuarios/registrar/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "profesional123",
    "email": "profesional@example.com",
    "password": "MiContraseña456!",
    "password_confirm": "MiContraseña456!",
    "first_name": "Profesional",
    "last_name": "Experto",
    "telefono": "+54 11 9876-5432",
    "rol": "profesional",
    "anios_experiencia": 5,
    "servicios": [1, 3],
    "horarios": [
      {
        "dia": "lunes",
        "hora_inicio": "09:00",
        "hora_fin": "18:00"
      },
      {
        "dia": "martes",
        "hora_inicio": "09:00",
        "hora_fin": "18:00"
      }
    ]
  }'
```

### Ejemplo 3: Modificar Perfil (Autenticado)

```python
import requests

url = "http://localhost:8000/api/usuarios/perfil/modificar/"

# Obtener token de sesión después de login
session = requests.Session()
session.post("http://localhost:8000/api/auth/login/", json={
    "email": "cliente@example.com",
    "password": "MiContraseña123!"
})

# Modificar perfil
data = {
    "telefono": "+54 11 9999-9999",
    "direccion": "Nueva dirección 456"
}

response = session.patch(url, json=data)

if response.status_code == 200:
    print("Perfil actualizado:", response.json())
else:
    print("Error:", response.json())
```

### Ejemplo 4: Eliminar Perfil

```python
import requests

url = "http://localhost:8000/api/usuarios/perfil/eliminar/"

session = requests.Session()
# ... (login previo)

data = {
    "confirmar": True,
    "password": "MiContraseña123!"
}

response = session.post(url, json=data)

if response.status_code == 200:
    print("Perfil eliminado:", response.json())
else:
    print("Error:", response.json())
```

### Ejemplo 5: Verificar si puede eliminar

```python
import requests

url = "http://localhost:8000/api/usuarios/perfil/puede-eliminar/"

session = requests.Session()
# ... (login previo)

response = session.get(url)
data = response.json()

if data["puede_eliminar"]:
    print("✓ Puede eliminar su perfil")
else:
    print("✗ No puede eliminar:", data["mensaje"])
```

---

## Códigos de Estado HTTP

- **200 OK**: Operación exitosa
- **201 CREATED**: Recurso creado exitosamente
- **400 BAD REQUEST**: Errores de validación
- **401 UNAUTHORIZED**: No autenticado
- **403 FORBIDDEN**: No autorizado (ej: contraseña incorrecta)
- **404 NOT FOUND**: Recurso no encontrado
- **500 INTERNAL SERVER ERROR**: Error del servidor

---

## Formato de Respuestas

Todas las respuestas siguen un formato estándar:

### Respuesta exitosa:
```json
{
  "success": true,
  "message": "Mensaje descriptivo",
  "data": { /* datos solicitados */ }
}
```

### Respuesta con error:
```json
{
  "success": false,
  "errors": ["Error 1", "Error 2"] // o { "campo": ["error"] }
}
```

---

## Seguridad

### Validaciones Implementadas

1. **Email**: Formato válido, unicidad
2. **Contraseña**: Complejidad mínima (8 caracteres, mayúscula, minúscula, número)
3. **Teléfono**: Formato válido (7-20 dígitos)
4. **Horarios**: Lógica (hora_inicio < hora_fin)
5. **Eliminación**: Verificación de condiciones (sin turnos/pagos activos)
6. **Modificación**: Confirmación con contraseña (usuarios no-Google)

### Protecciones

- Baja lógica (no física)
- Anonimización de datos personales
- Auditoría (ID y fecha de eliminación)
- Confirmación por email
- Tokens de confirmación (expiración 24 horas)
- Logging de operaciones críticas

---

## Configuración del Entorno

### Dependencias requeridas:

```txt
Django==5.2.7
djangorestframework==3.14.0
Pillow==10.0.0
requests==2.31.0
```

### Instalación:

```bash
pip install djangorestframework
```

### Configuración en settings.py:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Email (desarrollo)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@servihogar.com'
```

### Ejecutar migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Ejecutar servidor:

```bash
python manage.py runserver
```

---

## Contacto y Soporte

Para más información sobre la implementación o dudas técnicas, revisar el código fuente en:

- `apps/usuarios/api_views.py` - Endpoints REST
- `apps/usuarios/services.py` - Lógica de negocio
- `apps/usuarios/validators.py` - Validaciones
- `apps/usuarios/serializers.py` - Serializers
- `apps/usuarios/emails.py` - Gestión de emails

---

**Proyecto:** ServiHogar - Sistema de Gestión de Servicios del Hogar  
**Versión:** 1.0  
**Fecha:** Noviembre 2025
