# Guía de Instalación - Sistema de Gestión de Perfiles

## ServiHogar - Módulo de Usuarios

Esta guía te llevará paso a paso para instalar y ejecutar el sistema de gestión de perfiles de usuario.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.13** o superior
- **pip** (gestor de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)
- **Editor de código** (VS Code, PyCharm, etc.)

### Verificar instalación de Python

```bash
python --version
# Debería mostrar: Python 3.13.x o superior

pip --version
# Debería mostrar la versión de pip
```

---

## 🚀 Instalación Paso a Paso

### Paso 1: Navegar al Directorio del Proyecto

```bash
cd c:\Users\Usuario\Pictures\TF2025\servihogar4
```

### Paso 2: Crear Entorno Virtual (Recomendado)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Verás `(venv)` al inicio de tu línea de comandos, indicando que el entorno está activo.

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- Django 5.2.7
- djangorestframework 3.14.0
- Pillow 10.4.0
- requests 2.32.3

**Verificar instalación:**
```bash
pip list
```

Deberías ver las librerías listadas.

### Paso 4: Aplicar Migraciones de Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará las tablas necesarias en la base de datos SQLite.

**Salida esperada:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, usuarios, servicios, turnos, promociones, politicas, reportes
Running migrations:
  Applying usuarios.0001_initial... OK
  ...
```

### Paso 5: Crear Superusuario (Opcional pero Recomendado)

```bash
python manage.py createsuperuser
```

Completa los datos solicitados:
- **Username:** admin
- **Email:** admin@servihogar.com
- **Password:** (elige una contraseña segura)
- **Password (again):** (repite la contraseña)

### Paso 6: Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

**Salida esperada:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## ✅ Verificar que Todo Funciona

### Verificación 1: Acceder al Admin de Django

1. Abre tu navegador
2. Ve a: `http://127.0.0.1:8000/admin/`
3. Inicia sesión con las credenciales del superusuario
4. Deberías ver el panel de administración de Django

### Verificación 2: Probar la API

Abre una nueva terminal (manteniendo el servidor corriendo) y ejecuta:

```bash
curl http://127.0.0.1:8000/api/usuarios/registrar/
```

**Salida esperada:**
```json
{"detail": "Method \"GET\" not allowed."}
```

Esto es correcto, significa que la API está funcionando (solo acepta POST).

### Verificación 3: Registrar un Usuario de Prueba

```bash
curl -X POST http://127.0.0.1:8000/api/usuarios/registrar/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"test_cliente\", \"email\": \"test@example.com\", \"password\": \"TestPass123!\", \"password_confirm\": \"TestPass123!\", \"first_name\": \"Test\", \"last_name\": \"Usuario\", \"rol\": \"cliente\"}"
```

**Salida esperada:**
```json
{
  "success": true,
  "message": "Usuario registrado exitosamente. Por favor revisa tu email para confirmar tu cuenta.",
  "usuario": {
    "id": 1,
    "username": "test_cliente",
    "email": "test@example.com",
    ...
  }
}
```

**En la consola del servidor deberías ver el email de confirmación:**
```
Subject: ServiHogar - Confirma tu registro
...
```

---

## 🧪 Ejecutar Tests

Para verificar que todo el código funciona correctamente:

```bash
python manage.py test apps.usuarios.tests_services
```

**Salida esperada:**
```
...........................
----------------------------------------------------------------------
Ran 24 tests in 2.345s

OK
```

---

## 🔧 Configuración Adicional (Opcional)

### Configurar Email Real (Producción)

Edita `servihogar/settings.py`:

```python
# Reemplazar:
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Por (para Gmail):
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-aplicacion'
DEFAULT_FROM_EMAIL = 'noreply@servihogar.com'
```

**Nota:** Para Gmail, necesitas crear una "contraseña de aplicación" en tu cuenta de Google.

### Configurar Google OAuth (Opcional)

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto
3. Habilita Google OAuth API
4. Obtén Client ID y Client Secret
5. Edita `servihogar/settings.py`:

```python
GOOGLE_OAUTH_CLIENT_ID = 'tu-client-id.apps.googleusercontent.com'
GOOGLE_OAUTH_CLIENT_SECRET = 'tu-client-secret'
```

---

## 📖 Uso de la API

### Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/usuarios/registrar/` | Registrar nuevo usuario |
| GET | `/api/usuarios/confirmar/<uidb64>/<token>/` | Confirmar email |
| GET | `/api/usuarios/perfil/` | Obtener perfil (autenticado) |
| PATCH | `/api/usuarios/perfil/modificar/` | Modificar perfil |
| POST | `/api/usuarios/perfil/eliminar/` | Eliminar perfil |
| GET | `/api/usuarios/perfil/puede-eliminar/` | Verificar si puede eliminar |

### Ejemplo: Registrar un Cliente

**Con curl (Windows CMD):**
```bash
curl -X POST http://127.0.0.1:8000/api/usuarios/registrar/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"cliente123\", \"email\": \"cliente@example.com\", \"password\": \"MiPass123!\", \"password_confirm\": \"MiPass123!\", \"first_name\": \"Juan\", \"last_name\": \"Perez\", \"telefono\": \"+54 11 1234-5678\", \"rol\": \"cliente\"}"
```

**Con Python:**
```python
import requests

url = "http://127.0.0.1:8000/api/usuarios/registrar/"

data = {
    "username": "cliente123",
    "email": "cliente@example.com",
    "password": "MiPass123!",
    "password_confirm": "MiPass123!",
    "first_name": "Juan",
    "last_name": "Perez",
    "telefono": "+54 11 1234-5678",
    "rol": "cliente"
}

response = requests.post(url, json=data)
print(response.json())
```

### Ejemplo: Registrar un Profesional

```python
import requests

url = "http://127.0.0.1:8000/api/usuarios/registrar/"

data = {
    "username": "profesional123",
    "email": "prof@example.com",
    "password": "SecurePass456!",
    "password_confirm": "SecurePass456!",
    "first_name": "María",
    "last_name": "González",
    "telefono": "+54 11 9876-5432",
    "direccion": "Av. Principal 456",
    "rol": "profesional",
    "anios_experiencia": 5,
    "servicios": [1, 2, 3],  # IDs de servicios existentes
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

---

## 🐛 Solución de Problemas Comunes

### Error: "No module named 'rest_framework'"

**Solución:**
```bash
pip install djangorestframework
```

### Error: "Table doesn't exist"

**Solución:**
```bash
python manage.py migrate
```

### Error: "Port 8000 is already in use"

**Solución 1:** Cierra el otro servidor que está corriendo

**Solución 2:** Usa otro puerto:
```bash
python manage.py runserver 8080
```

### Los emails no se envían

**Solución:** En desarrollo, los emails se muestran en la consola donde corre el servidor. Busca allí el contenido del email.

### Error al crear usuario: "Password too weak"

**Solución:** Asegúrate de que la contraseña tenga:
- Mínimo 8 caracteres
- Al menos 1 mayúscula
- Al menos 1 minúscula
- Al menos 1 número

---

## 📚 Documentación Adicional

Después de la instalación, consulta:

- **`API_USUARIOS_DOCUMENTATION.md`** - Documentación completa de la API
- **`IMPLEMENTACION_USUARIOS.md`** - Guía de implementación detallada
- **`README_IMPLEMENTACION.md`** - Resumen ejecutivo

---

## 🔄 Comandos Útiles

### Crear migraciones después de cambios en modelos
```bash
python manage.py makemigrations
```

### Aplicar migraciones
```bash
python manage.py migrate
```

### Ejecutar tests
```bash
python manage.py test
```

### Ejecutar tests específicos
```bash
python manage.py test apps.usuarios.tests_services
```

### Abrir shell interactivo de Django
```bash
python manage.py shell
```

### Crear superusuario
```bash
python manage.py createsuperuser
```

### Ver estructura de tablas
```bash
python manage.py dbshell
.tables
.schema usuarios_usuario
```

### Cargar datos iniciales (fixtures)
```bash
python manage.py loaddata initial_data.json
```

---

## 🌐 Acceder desde otros dispositivos (LAN)

Para que otros dispositivos en tu red local puedan acceder:

### Paso 1: Obtener tu IP local

**Windows:**
```bash
ipconfig
# Busca "Dirección IPv4"
```

**Linux/Mac:**
```bash
ifconfig
# Busca "inet"
```

Ejemplo: `192.168.1.100`

### Paso 2: Agregar IP a ALLOWED_HOSTS

Edita `servihogar/settings.py`:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.100']
```

### Paso 3: Ejecutar servidor en todas las interfaces

```bash
python manage.py runserver 0.0.0.0:8000
```

### Paso 4: Acceder desde otro dispositivo

En otro dispositivo en la misma red, abre el navegador y ve a:
```
http://192.168.1.100:8000/
```

---

## 📊 Estructura de Directorios

```
servihogar4/
├── manage.py                         # Script de gestión Django
├── requirements.txt                  # Dependencias
├── db.sqlite3                        # Base de datos
├── README.md                         # Documentación general
├── API_USUARIOS_DOCUMENTATION.md    # Documentación API
├── IMPLEMENTACION_USUARIOS.md       # Guía de implementación
├── README_IMPLEMENTACION.md         # Resumen ejecutivo
├── GUIA_INSTALACION.md              # Esta guía
│
├── servihogar/                      # Configuración del proyecto
│   ├── settings.py                  # Configuración Django
│   ├── urls.py                      # URLs principales
│   └── wsgi.py                      # WSGI config
│
├── apps/                            # Aplicaciones Django
│   ├── usuarios/                    # App de usuarios
│   │   ├── models.py               # Modelos
│   │   ├── services.py             # ⭐ Lógica de negocio
│   │   ├── validators.py           # ⭐ Validaciones
│   │   ├── serializers.py          # ⭐ Serializers REST
│   │   ├── api_views.py            # ⭐ Endpoints REST
│   │   ├── api_urls.py             # ⭐ URLs API
│   │   ├── emails.py               # ⭐ Gestión de emails
│   │   ├── tests_services.py       # ⭐ Tests unitarios
│   │   ├── views.py                # Vistas Django
│   │   ├── urls.py                 # URLs Django
│   │   └── forms.py                # Formularios Django
│   │
│   ├── servicios/                   # App de servicios
│   ├── turnos/                      # App de turnos
│   ├── promociones/                 # App de promociones
│   ├── politicas/                   # App de políticas
│   └── reportes/                    # App de reportes
│
├── templates/                       # Plantillas HTML
├── static/                          # Archivos estáticos (CSS, JS, imágenes)
└── media/                           # Archivos subidos por usuarios

⭐ = Archivos nuevos de esta implementación
```

---

## ✅ Checklist de Instalación

Marca cada paso a medida que lo completes:

- [ ] Python 3.13+ instalado
- [ ] pip instalado
- [ ] Navegado al directorio del proyecto
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Migraciones aplicadas (`python manage.py migrate`)
- [ ] Superusuario creado (`python manage.py createsuperuser`)
- [ ] Servidor ejecutándose (`python manage.py runserver`)
- [ ] Admin de Django accesible (`http://127.0.0.1:8000/admin/`)
- [ ] API respondiendo (`curl http://127.0.0.1:8000/api/usuarios/registrar/`)
- [ ] Usuario de prueba creado exitosamente
- [ ] Tests ejecutados y pasando (`python manage.py test`)

Si todos los puntos están marcados, ¡la instalación fue exitosa! 🎉

---

## 🆘 Soporte

Si encuentras problemas durante la instalación:

1. **Revisa los logs** en la consola donde corre el servidor
2. **Consulta la documentación** en los archivos .md
3. **Ejecuta los tests** para verificar que todo funciona
4. **Verifica las versiones** de Python y las dependencias

---

## 🎉 ¡Listo para Usar!

Ahora que tienes todo instalado, puedes:

1. **Explorar la API** usando herramientas como Postman o curl
2. **Leer la documentación** completa en `API_USUARIOS_DOCUMENTATION.md`
3. **Revisar los ejemplos** en `IMPLEMENTACION_USUARIOS.md`
4. **Ejecutar los tests** para ver cómo funciona todo
5. **Desarrollar nuevas funcionalidades** sobre esta base

---

**¡Bienvenido a ServiHogar!** 🏠✨

---

**Documento:** Guía de Instalación  
**Versión:** 1.0  
**Fecha:** Noviembre 2025  
**Proyecto:** ServiHogar - Sistema de Gestión de Servicios del Hogar
