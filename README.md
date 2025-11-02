# 🏠 ServiHogar - Plataforma de Servicios del Hogar

Sistema completo en Django para conectar clientes con profesionales de servicios del hogar.

## 📋 Características

- **Gestión de Usuarios**: Registro, login (convencional y Google OAuth), perfiles de Cliente/Profesional/Administrador
- **Gestión de Turnos**: Solicitar, modificar, cancelar y calificar turnos
- **Gestión de Servicios**: Búsqueda de servicios por categoría, precio, ubicación
- **Gestión de Promociones**: Crear y aplicar promociones y descuentos
- **Gestión de Políticas**: Políticas de cancelación y reembolso
- **Reportes**: Estadísticas de preferencias de clientes, servicios populares, ingresos, desempeño de profesionales
- **Integración con APIs**:
  - Google OAuth para login
  - Google Maps para geolocalización
  - Mercado Pago para pagos

## 🚀 Instalación

### 1. Clonar el repositorio o usar el código existente

```bash
cd c:\Users\Usuario\Pictures\TF2025\servihogar4
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install django pillow requests
```

### 4. Configurar variables de entorno (settings.py)

Edita `servihogar/settings.py` y reemplaza las credenciales de las APIs:

```python
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID = 'tu-client-id-aqui'
GOOGLE_OAUTH_CLIENT_SECRET = 'tu-client-secret-aqui'

# Mercado Pago
MERCADO_PAGO_PUBLIC_KEY = 'tu-public-key-aqui'
MERCADO_PAGO_ACCESS_TOKEN = 'tu-access-token-aqui'

# Google Maps
GOOGLE_MAPS_API_KEY = 'tu-api-key-aqui'
```

### 5. Crear migraciones y aplicar

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

Completa los datos:
- Username: admin
- Email: admin@servihogar.com
- Password: (tu contraseña)
- Rol: administrador

### 7. Ejecutar servidor

```bash
python manage.py runserver
```

Accede a: http://127.0.0.1:8000/

## 📁 Estructura del Proyecto

```
servihogar4/
├── manage.py
├── servihogar/
│   ├── settings.py          # Configuración principal
│   ├── urls.py              # URLs principales
│   └── wsgi.py
├── apps/
│   ├── usuarios/            # CU-04 a CU-08: Gestión de usuarios
│   ├── turnos/              # CU-23 a CU-32: Gestión de turnos
│   ├── servicios/           # CU-40 a CU-41: Gestión de servicios
│   ├── promociones/         # CU-18 a CU-20, CU-45: Gestión de promociones
│   ├── politicas/           # CU-19, CU-22, CU-23, CU-25, CU-26, CU-46
│   ├── reportes/            # CU-34: Reportes
│   ├── calificaciones/      # Calificaciones de turnos
│   └── auditoria/           # Registro de auditoría
├── templates/               # Plantillas HTML
│   ├── base.html
│   ├── home.html
│   ├── usuarios/
│   ├── turnos/
│   ├── servicios/
│   ├── promociones/
│   ├── politicas/
│   └── reportes/
└── static/
    ├── css/
    │   └── styles.css       # Estilos CSS
    └── img/
```

## 👥 Roles del Sistema

### Cliente
- Buscar servicios
- Solicitar turnos
- Modificar/cancelar turnos
- Calificar servicios completados
- Ver historial de turnos
- Recibir promociones

### Profesional
- Gestionar servicios ofrecidos
- Confirmar/rechazar turnos
- Ver historial de turnos
- Consultar pagos recibidos

### Administrador
- Administrar usuarios
- Gestionar categorías y servicios
- Crear/modificar/eliminar políticas
- Gestionar promociones
- Generar reportes del sistema

## 🔑 Casos de Uso Implementados

### Gestión de Usuarios
- **CU-04**: Registrar Usuario
- **CU-05**: Modificar Usuario
- **CU-06**: Eliminar Usuario
- **CU-07**: Iniciar Sesión (convencional y Google OAuth)
- **CU-08**: Cerrar Sesión

### Gestión de Turnos
- **CU-23**: Solicitar Turno
- **CU-24**: Modificar Turno
- **CU-25**: Cancelar Turno
- **CU-26**: Calificar Turno
- **CU-31**: Ver Historial de Turnos
- **CU-32**: Buscar Turno

### Gestión de Servicios
- **CU-40**: Buscar Servicio
- **CU-41**: Buscar Categoría

### Gestión de Promociones
- **CU-18**: Registrar Promoción
- **CU-19**: Modificar Promoción
- **CU-20**: Eliminar Promoción
- **CU-45**: Buscar Promoción

### Gestión de Políticas
- **CU-19**: Registrar Política de Reembolso
- **CU-22**: Modificar Política de Reembolso
- **CU-23**: Eliminar Política de Reembolso
- **CU-25**: Modificar Política de Cancelación
- **CU-26**: Eliminar Política de Cancelación
- **CU-46**: Buscar Política

### Reportes
- **CU-34**: Generar Reporte de Preferencias y Comportamientos de Cliente
- Reporte de Servicios Populares
- Reporte de Ingresos
- Reporte de Desempeño de Profesionales

## 🔧 Tecnologías Utilizadas

- **Backend**: Django 5.2.7
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: HTML5, CSS3 puro
- **APIs externas**:
  - Google OAuth 2.0
  - Google Maps JavaScript API
  - Mercado Pago API

## 📝 Notas Importantes

1. **Migraciones**: Cada vez que modifiques un modelo, ejecuta:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Archivos estáticos**: En producción, ejecuta:
   ```bash
   python manage.py collectstatic
   ```

3. **Seguridad**: Antes de deploy en producción:
   - Cambia `DEBUG = False` en settings.py
   - Actualiza `SECRET_KEY`
   - Configura `ALLOWED_HOSTS`
   - Usa variables de entorno para credenciales sensibles

## 🎯 URLs Principales

- **Home**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/
- **Login**: http://127.0.0.1:8000/usuarios/login/
- **Registro**: http://127.0.0.1:8000/usuarios/registrar/
- **Servicios**: http://127.0.0.1:8000/servicios/buscar/
- **Solicitar Turno**: http://127.0.0.1:8000/turnos/solicitar/
- **Historial**: http://127.0.0.1:8000/turnos/historial/
- **Reportes**: http://127.0.0.1:8000/reportes/

## 🤝 Contribución

Este es un proyecto académico para el Trabajo Final 2025.

## 📄 Licencia

Proyecto educativo - ServiHogar 2025
