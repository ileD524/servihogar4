# ServiHogar - Sistema de Gestión de Servicios del Hogar

Plataforma web desarrollada en Django para la gestión integral de servicios del hogar, conectando clientes con profesionales mediante un sistema de turnos, calificaciones y pagos.

## 🆕 Nueva Implementación: API REST para Gestión de Perfiles

Se ha implementado un sistema completo de **API REST** para la gestión de perfiles de usuario (CU-01, CU-02, CU-03) con:

- ✅ **Registro de usuarios** (manual y Google OAuth)
- ✅ **Confirmación por email** con tokens seguros
- ✅ **Modificación de perfil** con validaciones exhaustivas
- ✅ **Eliminación de perfil** con baja lógica y anonimización
- ✅ **Arquitectura limpia** (Servicios, Validadores, Serializers)
- ✅ **24 tests unitarios** con buena cobertura
- ✅ **Documentación completa** con ejemplos de uso

**📚 Documentación disponible:**
- [**GUIA_INSTALACION.md**](GUIA_INSTALACION.md) - Instalación paso a paso
- [**API_USUARIOS_DOCUMENTATION.md**](API_USUARIOS_DOCUMENTATION.md) - Documentación completa de la API
- [**IMPLEMENTACION_USUARIOS.md**](IMPLEMENTACION_USUARIOS.md) - Guía de implementación técnica
- [**README_IMPLEMENTACION.md**](README_IMPLEMENTACION.md) - Resumen ejecutivo

**🚀 Quick Start API:**
```bash
# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Ejecutar servidor
python manage.py runserver

# La API está disponible en: http://localhost:8000/api/usuarios/
```

---

## Descripción General

ServiHogar es una aplicación web que permite la administración completa de servicios domésticos. El sistema gestiona usuarios con diferentes roles (clientes, profesionales y administradores), servicios organizados por categorías, solicitud y seguimiento de turnos, aplicación de promociones, políticas de cancelación y generación de reportes estadísticos.

## Funcionalidades Principales

### Gestión de Usuarios ⭐ MEJORADO
Sistema completo de autenticación y administración de usuarios con tres roles diferenciados: clientes que solicitan servicios, profesionales que los ofrecen y administradores que gestionan la plataforma. 

**Nuevas características:**
- **API REST completa** para registro, modificación y eliminación de perfiles
- **Autenticación por Google OAuth** integrada
- **Sistema de confirmación por email** con tokens seguros (expiran en 24h)
- **Validaciones robustas** (email único, contraseña segura, formato de teléfono)
- **Baja lógica** con anonimización de datos personales
- **Auditoría completa** de operaciones de usuario
- **Separación de responsabilidades** (Servicios, Validadores, Serializers)

El sistema implementa control de acceso basado en roles con decoradores personalizados. Incluye registro, login convencional y por Google, modificación de perfiles, activación y desactivación de cuentas. Los usuarios pueden subir fotos de perfil y gestionar su información personal.

### Gestión de Servicios y Categorías
Los servicios se organizan en categorías para facilitar su búsqueda y gestión. Cada servicio tiene nombre, descripción, precio base, duración estimada y está asociado a un profesional. El sistema permite crear, modificar y desactivar tanto servicios como categorías. Implementa validación de dependencias: al desactivar una categoría, todos sus servicios asociados se desactivan automáticamente. Incluye búsqueda avanzada con filtros por nombre, categoría y estado, además de ordenamiento por múltiples columnas.

### Gestión de Turnos
Sistema completo para el ciclo de vida de los turnos: solicitud por parte del cliente, confirmación o rechazo por el profesional, modificación de fecha/hora, cancelación con validación de políticas, y calificación posterior al servicio completado. Los turnos tienen estados (pendiente, confirmado, cancelado, completado) y se validan horarios disponibles, profesionales activos y servicios vigentes. Incluye historial completo de turnos con filtros por fecha, servicio y estado.

### Gestión de Promociones
Creación y administración de códigos promocionales con descuentos porcentuales o montos fijos. Las promociones tienen fecha de inicio y fin, límite de usos, y pueden ser de tipo público o privado. El sistema valida automáticamente la vigencia, disponibilidad y aplicabilidad de cada promoción al momento de solicitar un turno.

### Políticas de Cancelación
Definición de políticas que establecen plazos mínimos de cancelación y porcentajes de reembolso según el tiempo de anticipación. Las políticas se aplican automáticamente al cancelar turnos y determinan si corresponde reembolso total, parcial o ninguno.

### Sistema de Reportes
Generación de reportes estadísticos sobre el funcionamiento de la plataforma: preferencias y comportamiento de clientes, servicios más solicitados, ingresos generados por período, y desempeño de profesionales (cantidad de servicios, calificación promedio, ingresos).

### Auditoría de Fechas
Todos los registros principales (usuarios, servicios, categorías) implementan seguimiento de fechas de creación, modificación y eliminación lógica. Esto permite trazabilidad completa de cambios y la posibilidad de reactivar registros previamente desactivados.

## Tecnologías Utilizadas

- Backend: Django 5.2.7
- **API REST: Django REST Framework 3.14.0** ⭐ NUEVO
- Base de datos: SQLite
- Frontend: HTML5, CSS3
- Python: 3.13.9
- Pillow: para manejo de imágenes
- Requests: para integraciones con APIs externas

## Estructura del Proyecto

```
servihogar4/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── README.md                         # Este archivo
├── GUIA_INSTALACION.md              # ⭐ Guía de instalación paso a paso
├── API_USUARIOS_DOCUMENTATION.md    # ⭐ Documentación completa de la API
├── IMPLEMENTACION_USUARIOS.md       # ⭐ Guía de implementación técnica
├── README_IMPLEMENTACION.md         # ⭐ Resumen ejecutivo
├── servihogar/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── usuarios/
│   │   ├── models.py
│   │   ├── services.py             # ⭐ Lógica de negocio
│   │   ├── validators.py           # ⭐ Validaciones
│   │   ├── serializers.py          # ⭐ Serializers REST
│   │   ├── api_views.py            # ⭐ Endpoints REST
│   │   ├── api_urls.py             # ⭐ URLs de la API
│   │   ├── emails.py               # ⭐ Gestión de emails
│   │   ├── tests_services.py       # ⭐ Tests unitarios
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── forms.py
│   ├── servicios/
│   ├── turnos/
│   ├── promociones/
│   ├── politicas/
│   └── reportes/
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── usuarios/
│   ├── servicios/
│   ├── turnos/
│   ├── promociones/
│   ├── politicas/
│   └── reportes/
├── static/
│   ├── css/
│   │   ├── styles.css
│   │   └── gestion-comun.css
│   └── img/
└── media/
    └── usuarios/

⭐ = Archivos nuevos de la implementación API REST
```

## Instalación y Configuración

### Requisitos Previos
- Python 3.13 o superior
- pip para gestión de paquetes

### Pasos de Instalación

1. Clonar o descargar el proyecto:
```bash
# Si usas Git
git clone <url-del-repositorio>
cd servihogar4

# O descargar y descomprimir el archivo ZIP, luego navegar al directorio
cd servihogar4
```

2. Crear y activar entorno virtual:

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

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

Si no existe el archivo `requirements.txt`, instalar manualmente:
```bash
pip install django pillow requests
```

4. Aplicar migraciones de base de datos:
```bash
python manage.py migrate
```

5. Crear superusuario administrador:
```bash
python manage.py createsuperuser
```
Completar los datos solicitados:
- Username: (elegir nombre de usuario)
- Email: (correo electrónico)
- Password: (contraseña segura)
- Rol: administrador

6. Ejecutar servidor de desarrollo:
```bash
python manage.py runserver
```

Para acceder desde otros dispositivos en la misma red:
```bash
python manage.py runserver 0.0.0.0:8000
```

7. Acceder a la aplicación:
- Desde el mismo equipo: `http://127.0.0.1:8000/`
- Desde otros dispositivos: `http://<IP-del-servidor>:8000/`
- Panel de administración: `http://127.0.0.1:8000/admin/`

**Nota:** Para permitir acceso desde otros dispositivos, agregar la IP del servidor en `servihogar/settings.py`:
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '<tu-IP-local>']
```

## Roles y Permisos

### Cliente
- Visualizar y buscar servicios disponibles
- Solicitar turnos con profesionales
- Modificar turnos pendientes
- Cancelar turnos según políticas
- Calificar servicios completados
- Ver historial personal de turnos
- Aplicar códigos promocionales

### Profesional
- Gestionar servicios propios
- Confirmar o rechazar solicitudes de turnos
- Ver agenda de turnos
- Consultar historial de servicios prestados
- Visualizar calificaciones recibidas

### Administrador
- Gestión completa de usuarios (crear, modificar, activar/desactivar)
- Gestión de categorías de servicios
- Gestión de servicios de todos los profesionales
- Creación y modificación de promociones
- Definición de políticas de cancelación
- Generación de reportes estadísticos
- Acceso total al sistema


## Trabajo Futuro

El sistema está diseñado para permitir futuras integraciones con APIs externas como Google OAuth para autenticación, Google Maps para geolocalización de servicios, y Mercado Pago para procesamiento de pagos online.

## Información del Proyecto

Proyecto académico desarrollado para Trabajo Final 2025.
Sistema de gestión completo con arquitectura modular y escalable.
