# ServiHogar - Sistema de Gestión de Servicios del Hogar

Plataforma web desarrollada en Django para la gestión integral de servicios del hogar, conectando clientes con profesionales mediante un sistema de turnos, calificaciones y pagos.

## Descripción General

ServiHogar es una aplicación web que permite la administración completa de servicios domésticos. El sistema gestiona usuarios con diferentes roles (clientes, profesionales y administradores), servicios organizados por categorías, solicitud y seguimiento de turnos, aplicación de promociones, políticas de cancelación y generación de reportes estadísticos.

## Funcionalidades Principales

### Gestión de Usuarios
Sistema completo de autenticación y administración de usuarios con tres roles diferenciados: clientes que solicitan servicios, profesionales que los ofrecen y administradores que gestionan la plataforma. Incluye registro, login convencional, modificación de perfiles, activación y desactivación de cuentas. Los usuarios pueden subir fotos de perfil y gestionar su información personal. El sistema implementa control de acceso basado en roles con decoradores personalizados.

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
├── servihogar/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── usuarios/
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
