# Implementación de Gestión de Perfiles de Usuario

## ServiHogar - Casos de Uso CU-01, CU-02, CU-03

Esta documentación técnica describe la implementación completa de los casos de uso de gestión de perfiles siguiendo una arquitectura MVC/REST con buenas prácticas, validaciones robustas y separación de responsabilidades.

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Casos de Uso Implementados](#casos-de-uso-implementados)
4. [Estructura de Archivos](#estructura-de-archivos)
5. [Instalación y Configuración](#instalación-y-configuración)
6. [Uso de la API](#uso-de-la-api)
7. [Validaciones](#validaciones)
8. [Manejo de Errores](#manejo-de-errores)
9. [Seguridad](#seguridad)

---

## 🎯 Visión General

Esta implementación cubre tres casos de uso fundamentales para la gestión de perfiles:

- **CU-01: Registrar Perfil** - Registro manual o con Google OAuth
- **CU-02: Eliminar Perfil** - Baja lógica con validaciones de negocio
- **CU-03: Modificar Perfil** - Actualización de datos con validaciones

### Características Principales

✅ Arquitectura limpia con separación de capas  
✅ API REST completa con endpoints documentados  
✅ Validaciones exhaustivas de datos  
✅ Manejo robusto de errores  
✅ Integración opcional con Google OAuth  
✅ Sistema de confirmación por email  
✅ Baja lógica (no física) con anonimización  
✅ Auditoría de operaciones  
✅ Logging completo  
✅ Mensajes de error en español  

---

## 🏗️ Arquitectura

### Patrón de Diseño

La implementación sigue una arquitectura en capas con responsabilidades bien definidas:

```
┌────────────────────────────────────────────────────────┐
│                     API Layer                          │
│  api_views.py - Endpoints REST + Autenticación         │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│                  Validation Layer                      │
│  serializers.py - Validación de entrada/salida         │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│                   Business Layer                       │
│  services.py - Lógica de negocio                       │
│  validators.py - Validaciones específicas              │
│  emails.py - Gestión de emails                         │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│                   Persistence Layer                    │
│  models.py - Modelos Django ORM                        │
└────────────────────────────────────────────────────────┘
```

### Principios SOLID Aplicados

1. **Single Responsibility**: Cada clase/módulo tiene una única responsabilidad
2. **Open/Closed**: Extensible sin modificar código existente
3. **Liskov Substitution**: Los servicios pueden intercambiarse
4. **Interface Segregation**: Interfaces específicas por funcionalidad
5. **Dependency Inversion**: Dependencias hacia abstracciones

---

## 📝 Casos de Uso Implementados

### CU-01: Registrar Perfil

**Actor:** Usuario no registrado

**Flujo Principal:**

1. Usuario selecciona tipo (Cliente/Profesional)
2. Elige método: Manual o Google OAuth
3. Completa formulario con datos requeridos
4. Sistema valida formato y unicidad de email
5. Sistema valida criterios de contraseña segura
6. Sistema crea usuario en estado "Pendiente"
7. Sistema envía email de confirmación
8. Usuario hace clic en enlace del email
9. Sistema cambia estado a "Activo"

**Flujo Alternativo (Google OAuth):**

1. Usuario autentica con Google
2. Sistema obtiene nombre y email de Google
3. Sistema crea usuario en estado "Activo"
4. Usuario puede completar datos adicionales posteriormente

**Validaciones:**

- Email: formato RFC 5322, unicidad
- Contraseña: 8+ caracteres, mayúscula, minúscula, número
- Teléfono: 7-20 dígitos, formato internacional
- Profesionales: servicios y horarios requeridos
- Horarios: hora_inicio < hora_fin

**Endpoints:**

- `POST /api/usuarios/registrar/` - Registro manual
- `POST /api/usuarios/registrar/google/` - Registro Google
- `PUT /api/usuarios/completar-datos/` - Completar datos Google
- `GET /api/usuarios/confirmar/<uidb64>/<token>/` - Confirmar email

---

### CU-02: Eliminar Perfil

**Actor:** Cliente o Profesional autenticado

**Precondiciones:**

- Usuario debe estar autenticado
- No tener turnos en estado: pendiente, confirmado, en_curso
- No tener pagos pendientes

**Flujo Principal:**

1. Usuario solicita eliminar perfil
2. Sistema valida precondiciones
3. Sistema requiere confirmación explícita
4. Para usuarios con contraseña: verificar contraseña
5. Sistema realiza baja lógica
6. Sistema anonimiza datos personales
7. Sistema mantiene ID y fecha para auditoría
8. Sistema envía email de confirmación de baja

**Validaciones:**

- Verificar ausencia de turnos activos
- Verificar ausencia de pagos pendientes
- Confirmar identidad (contraseña si aplica)

**Efectos:**

- `activo`: false
- `is_active`: false
- `fecha_eliminacion`: timestamp actual
- Datos personales: anonimizados
- Foto perfil: eliminada
- Servicios/horarios: desasociados

**Endpoints:**

- `GET /api/usuarios/perfil/puede-eliminar/` - Verificar condiciones
- `POST /api/usuarios/perfil/eliminar/` - Eliminar perfil

---

### CU-03: Modificar Perfil

**Actor:** Cliente o Profesional autenticado

**Precondiciones:**

- Usuario debe estar autenticado

**Flujo Principal:**

1. Sistema carga datos actuales en formulario
2. Usuario modifica campos deseados
3. Sistema valida formato de datos
4. Si cambia email: validar formato y unicidad
5. Sistema guarda cambios en BD
6. Sistema actualiza fecha_modificacion
7. Para profesionales: actualiza servicios/horarios
8. Sistema envía email de notificación

**Validaciones:**

- Email: formato válido, único (excepto propio)
- Teléfono: formato válido
- Horarios (profesionales): formato y lógica correctos

**Campos Modificables:**

**Cliente/Profesional:**
- first_name
- last_name
- email
- telefono
- direccion
- foto_perfil

**Solo Profesional:**
- anios_experiencia
- servicios (lista de IDs)
- horarios (lista de objetos)

**Endpoints:**

- `GET /api/usuarios/perfil/` - Obtener datos actuales
- `PUT /api/usuarios/perfil/modificar/` - Actualización completa
- `PATCH /api/usuarios/perfil/modificar/` - Actualización parcial

---

## 📁 Estructura de Archivos

```
apps/usuarios/
├── models.py              # Modelos: Usuario, Cliente, Profesional, HorarioDisponibilidad
├── services.py            # ⭐ Lógica de negocio (CU-01, CU-02, CU-03)
├── validators.py          # ⭐ Validaciones de negocio
├── serializers.py         # ⭐ Serializers REST
├── api_views.py           # ⭐ Endpoints REST
├── api_urls.py            # ⭐ URLs de la API
├── emails.py              # ⭐ Gestión de emails
├── views.py               # Vistas tradicionales Django
├── urls.py                # URLs tradicionales
├── forms.py               # Formularios Django
└── admin.py               # Configuración Django Admin

⭐ = Archivos nuevos creados para esta implementación
```

---

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install Django==5.2.7
pip install djangorestframework==3.14.0
pip install Pillow==10.4.0
pip install requests==2.32.3
```

### 2. Configurar settings.py

El archivo `servihogar/settings.py` ya está configurado con:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'apps.usuarios',
    # ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Email (desarrollo - muestra emails en consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@servihogar.com'
```

### 3. Aplicar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Crear Superusuario (Opcional)

```bash
python manage.py createsuperuser
```

### 5. Ejecutar Servidor

```bash
python manage.py runserver
```

La API estará disponible en: `http://localhost:8000/api/usuarios/`

---

## 🔌 Uso de la API

### Autenticación

La API usa autenticación por sesión de Django. Para endpoints que requieren autenticación, primero debes iniciar sesión.

#### Iniciar Sesión (Tradicional)

```python
import requests

session = requests.Session()

# Login
login_url = "http://localhost:8000/usuarios/login/"
session.post(login_url, data={
    "email": "usuario@example.com",
    "password": "MiContraseña123!"
})

# Ahora puedes hacer requests autenticados
response = session.get("http://localhost:8000/api/usuarios/perfil/")
```

### Ejemplos de Uso

#### 1. Registrar Cliente

```python
import requests

url = "http://localhost:8000/api/usuarios/registrar/"

data = {
    "username": "cliente_nuevo",
    "email": "cliente@example.com",
    "password": "Segura123!",
    "password_confirm": "Segura123!",
    "first_name": "Juan",
    "last_name": "Pérez",
    "telefono": "+54 11 1234-5678",
    "direccion": "Av. Ejemplo 123",
    "rol": "cliente"
}

response = requests.post(url, json=data)
print(response.json())
```

#### 2. Registrar Profesional

```python
import requests

url = "http://localhost:8000/api/usuarios/registrar/"

data = {
    "username": "profesional_nuevo",
    "email": "profesional@example.com",
    "password": "Segura456!",
    "password_confirm": "Segura456!",
    "first_name": "María",
    "last_name": "González",
    "telefono": "+54 11 9876-5432",
    "rol": "profesional",
    "anios_experiencia": 5,
    "servicios": [1, 2, 3],  # IDs de servicios
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
}

response = requests.post(url, json=data)
print(response.json())
```

#### 3. Modificar Perfil

```python
import requests

session = requests.Session()
# ... (login previo)

url = "http://localhost:8000/api/usuarios/perfil/modificar/"

data = {
    "telefono": "+54 11 9999-9999",
    "direccion": "Nueva dirección 456"
}

response = session.patch(url, json=data)
print(response.json())
```

#### 4. Eliminar Perfil

```python
import requests

session = requests.Session()
# ... (login previo)

# Primero verificar si puede eliminar
check_url = "http://localhost:8000/api/usuarios/perfil/puede-eliminar/"
check_response = session.get(check_url)
print(check_response.json())

# Si puede eliminar, proceder
if check_response.json()["puede_eliminar"]:
    delete_url = "http://localhost:8000/api/usuarios/perfil/eliminar/"
    data = {
        "confirmar": True,
        "password": "MiContraseña123!"
    }
    response = session.post(delete_url, json=data)
    print(response.json())
```

---

## ✅ Validaciones

### Validaciones de Email

```python
# validators.py - UsuarioValidator.validar_email_formato()

✓ Formato RFC 5322
✓ Dominio válido
✓ No permite espacios
✓ Unicidad (no duplicados)

Ejemplos válidos:
- usuario@example.com
- nombre.apellido@empresa.com.ar
- admin+test@domain.co

Ejemplos inválidos:
- usuario@
- @example.com
- usuario @example.com
```

### Validaciones de Contraseña

```python
# validators.py - UsuarioValidator.validar_contrasena_segura()

✓ Mínimo 8 caracteres
✓ Al menos 1 mayúscula
✓ Al menos 1 minúscula
✓ Al menos 1 número
✓ No puede ser muy común (validador Django)
✓ No puede ser muy similar a datos del usuario

Ejemplos válidos:
- Segura123
- MiContraseña456!
- PassWord789

Ejemplos inválidos:
- password (sin mayúscula ni número)
- PASSWORD123 (sin minúscula)
- Password (sin número)
- Pass1 (muy corta)
```

### Validaciones de Teléfono

```python
# validators.py - UsuarioValidator.validar_telefono()

✓ 7-20 dígitos
✓ Permite: números, espacios, guiones, paréntesis, +
✓ Formato internacional

Ejemplos válidos:
- +54 11 1234-5678
- (011) 9876-5432
- 1234567890
- +1-555-123-4567

Ejemplos inválidos:
- 12345 (muy corto)
- abc123 (letras)
- +++ (solo símbolos)
```

### Validaciones de Horarios

```python
# validators.py - UsuarioValidator.validar_horarios()

✓ Día válido (lunes-domingo)
✓ Formato HH:MM
✓ hora_inicio < hora_fin
✓ Al menos 1 horario

Ejemplo válido:
{
    "dia": "lunes",
    "hora_inicio": "09:00",
    "hora_fin": "18:00"
}

Ejemplos inválidos:
- hora_inicio: "18:00", hora_fin: "09:00" (invertidos)
- dia: "lunees" (día inválido)
- hora_inicio: "25:00" (formato inválido)
```

---

## ⚠️ Manejo de Errores

### Formato Estándar de Errores

Todas las respuestas de error siguen este formato:

```json
{
  "success": false,
  "errors": {
    "campo1": ["Error en campo1"],
    "campo2": ["Error en campo2"]
  }
}
```

O para errores generales:

```json
{
  "success": false,
  "errors": ["Mensaje de error general"]
}
```

### Códigos HTTP

| Código | Significado | Cuándo se usa |
|--------|-------------|---------------|
| 200 | OK | Operación exitosa |
| 201 | Created | Recurso creado |
| 400 | Bad Request | Error de validación |
| 401 | Unauthorized | No autenticado |
| 403 | Forbidden | No autorizado |
| 404 | Not Found | Recurso no existe |
| 500 | Server Error | Error interno |

### Ejemplos de Errores Comunes

#### Error de validación de email

```json
{
  "success": false,
  "errors": {
    "email": ["Ya existe un usuario registrado con este email"]
  }
}
```

#### Error de contraseña débil

```json
{
  "success": false,
  "errors": {
    "password": [
      "La contraseña debe tener al menos 8 caracteres",
      "La contraseña debe contener al menos una letra mayúscula"
    ]
  }
}
```

#### Error al eliminar perfil

```json
{
  "success": false,
  "errors": [
    "No puede eliminar su perfil porque tiene turnos activos o pendientes"
  ]
}
```

---

## 🔒 Seguridad

### Medidas Implementadas

1. **Contraseñas Hasheadas**
   - Django usa PBKDF2 por defecto
   - Nunca se almacenan en texto plano

2. **Validación de Tokens**
   - Tokens de confirmación de email con expiración
   - Tokens únicos por usuario

3. **Baja Lógica**
   - No se eliminan físicamente los registros
   - Se anonimiza la información personal
   - Se mantiene auditoría

4. **Validación de Permisos**
   - Solo usuarios autenticados pueden modificar su perfil
   - No se puede modificar el perfil de otro usuario
   - Administradores tienen permisos separados

5. **Confirmación Adicional**
   - Eliminación requiere contraseña
   - Confirmación explícita con flag booleano

6. **CSRF Protection**
   - Django CSRF middleware activo
   - Tokens CSRF en formularios

7. **Logging**
   - Todas las operaciones críticas se registran
   - Nivel INFO para operaciones exitosas
   - Nivel ERROR para fallos

### Ejemplo de Log

```
INFO 2025-11-05 10:30:00 apps.usuarios.services: Usuario juanperez registrado exitosamente (pendiente de confirmación)
INFO 2025-11-05 10:35:00 apps.usuarios.emails: Email de confirmación enviado a juan@example.com
INFO 2025-11-05 10:40:00 apps.usuarios.services: Email confirmado para usuario juanperez
INFO 2025-11-05 11:15:00 apps.usuarios.services: Perfil actualizado para usuario juanperez
INFO 2025-11-05 15:30:00 apps.usuarios.services: Perfil eliminado para usuario ID 123
```

---

## 📧 Sistema de Emails

### Emails Implementados

1. **Email de Confirmación** (CU-01)
   - Se envía al registrarse
   - Contiene enlace de activación
   - Expira en 24 horas

2. **Email de Bienvenida** (CU-01)
   - Se envía al confirmar email
   - Personalizado según rol

3. **Email de Actualización** (CU-03)
   - Se envía al modificar perfil
   - Alerta de seguridad

4. **Email de Baja** (CU-02)
   - Se envía al eliminar perfil
   - Confirmación de eliminación

### Configuración

**Desarrollo (consola):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Los emails se muestran en la consola donde corre el servidor.

**Producción (SMTP):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-app'
DEFAULT_FROM_EMAIL = 'noreply@servihogar.com'
```

---

## 🧪 Testing

### Pruebas Manuales Recomendadas

#### Test 1: Registro exitoso de cliente

```bash
curl -X POST http://localhost:8000/api/usuarios/registrar/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_cliente",
    "email": "cliente@test.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "first_name": "Test",
    "last_name": "Cliente",
    "rol": "cliente"
  }'
```

**Resultado esperado:** 201 Created + email en consola

#### Test 2: Email duplicado

```bash
# Registrar dos veces el mismo email
# Segunda vez debe fallar
```

**Resultado esperado:** 400 Bad Request + error de email duplicado

#### Test 3: Contraseña débil

```bash
curl -X POST http://localhost:8000/api/usuarios/registrar/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_debil",
    "email": "debil@test.com",
    "password": "12345",
    "password_confirm": "12345",
    "first_name": "Test",
    "last_name": "Debil",
    "rol": "cliente"
  }'
```

**Resultado esperado:** 400 Bad Request + errores de contraseña

#### Test 4: Modificar perfil autenticado

1. Login
2. Modificar teléfono
3. Verificar cambio

**Resultado esperado:** 200 OK + datos actualizados

#### Test 5: Eliminar con turnos activos

1. Crear turno pendiente
2. Intentar eliminar perfil
3. Debe fallar

**Resultado esperado:** 400 Bad Request + mensaje explicativo

---

## 📚 Documentación Adicional

Para más detalles, consultar:

- **API_USUARIOS_DOCUMENTATION.md** - Documentación completa de la API
- **README.md** - Documentación general del proyecto
- Código fuente comentado en español

---

## 🤝 Buenas Prácticas Aplicadas

### 1. Separación de Responsabilidades

✅ Vistas solo manejan requests/responses  
✅ Servicios contienen lógica de negocio  
✅ Validadores encapsulan reglas  
✅ Models solo para persistencia  

### 2. DRY (Don't Repeat Yourself)

✅ Validaciones reutilizables  
✅ Servicios compartidos  
✅ Serializers evitan duplicación  

### 3. Clean Code

✅ Nombres descriptivos en español  
✅ Funciones pequeñas y específicas  
✅ Comentarios explicativos  
✅ Docstrings completos  

### 4. Manejo de Errores

✅ Try/except en todos los servicios  
✅ Mensajes descriptivos en español  
✅ Logging de errores  
✅ Rollback automático en transacciones  

### 5. Seguridad

✅ Validación de entrada  
✅ Sanitización de datos  
✅ Autenticación requerida  
✅ Baja lógica  

---

## 📞 Soporte

Para preguntas o problemas:

1. Revisar logs en consola
2. Verificar configuración en `settings.py`
3. Consultar documentación de API
4. Revisar código fuente comentado

---

**Proyecto:** ServiHogar  
**Módulo:** Gestión de Perfiles de Usuario  
**Versión:** 1.0  
**Fecha:** Noviembre 2025  
**Arquitectura:** MVC/REST con Django + DRF
