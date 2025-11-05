# API REST - Reportes, Estadísticas y Búsqueda

## Descripción General

Esta API REST implementa los endpoints para la gestión administrativa de reportes, estadísticas y búsqueda de promociones (CU-16, CU-30, CU-31, CU-40) en el sistema ServiHogar. Todos los endpoints requieren autenticación como **Administrador**.

## Autenticación

Todos los endpoints requieren:
- Token JWT en el header: `Authorization: Bearer <token>`
- Usuario con rol `administrador`

## Casos de Uso Implementados

### CU-16: Consultar Estadísticas
- ✅ Múltiples tipos de estadísticas (usuarios, servicios, ingresos, calificaciones)
- ✅ Períodos predefinidos y personalizados
- ✅ Métricas relevantes y agregadas
- ✅ Manejo de errores robusto

### CU-30: Generar Reporte de Profesionales
- ✅ Filtrado por servicio, calificación, antigüedad
- ✅ Análisis de desempeño completo
- ✅ Métricas de ingresos y calificaciones
- ✅ Opción de guardar reporte

### CU-31: Generar Reporte de Preferencias de Clientes
- ✅ Análisis de servicios solicitados
- ✅ Patrones horarios y de reserva
- ✅ Segmentación de clientes
- ✅ Análisis de cancelaciones

### CU-40: Buscar Promoción
- ✅ Búsqueda por múltiples criterios
- ✅ Filtros combinables
- ✅ Detalle completo de promociones
- ✅ Paginación de resultados

---

## Endpoints

## 1. Consultar Estadísticas (CU-16)

### Estadísticas del Sistema

**Endpoint:** `GET /api/reportes/estadisticas/`

**Descripción:** Consulta estadísticas del sistema según tipo y período.

**Query Parameters:**
- `tipo` (string, **requerido**): Tipo de estadística
  - Valores: `usuarios`, `servicios`, `ingresos`, `calificaciones`
- `periodo` (string, opcional): Período de análisis
  - Valores: `mes`, `trimestre`, `anio`, `personalizado`
  - Default: `mes`
- `fecha_inicio` (datetime, condicional): Inicio del período personalizado (ISO 8601)
  - Requerido si `periodo=personalizado`
- `fecha_fin` (datetime, condicional): Fin del período personalizado (ISO 8601)
  - Requerido si `periodo=personalizado`

**Ejemplos de Request:**

```bash
# Estadísticas de usuarios del último mes
GET /api/reportes/estadisticas/?tipo=usuarios&periodo=mes

# Estadísticas de ingresos del último trimestre
GET /api/reportes/estadisticas/?tipo=ingresos&periodo=trimestre

# Estadísticas personalizadas
GET /api/reportes/estadisticas/?tipo=servicios&periodo=personalizado&fecha_inicio=2025-01-01T00:00:00Z&fecha_fin=2025-03-31T23:59:59Z
```

**Respuesta Exitosa (200 OK) - Usuarios:**
```json
{
  "success": true,
  "tipo": "usuarios",
  "data": {
    "total_usuarios": 150,
    "usuarios_por_rol": [
      {
        "rol": "cliente",
        "cantidad": 100
      },
      {
        "rol": "profesional",
        "cantidad": 45
      },
      {
        "rol": "administrador",
        "cantidad": 5
      }
    ],
    "usuarios_activos": 85,
    "nuevos_usuarios": 25,
    "usuarios_por_dia": [
      {
        "dia": "2025-10-01T00:00:00Z",
        "cantidad": 3
      }
    ],
    "periodo": {
      "inicio": "2025-10-05T00:00:00Z",
      "fin": "2025-11-05T00:00:00Z"
    }
  }
}
```

**Respuesta Exitosa (200 OK) - Servicios:**
```json
{
  "success": true,
  "tipo": "servicios",
  "data": {
    "total_servicios": 45,
    "servicios_populares": [
      {
        "servicio__id": 1,
        "servicio__nombre": "Limpieza General",
        "servicio__categoria__nombre": "Limpieza",
        "cantidad_solicitudes": 125,
        "calificacion_promedio": 4.7
      }
    ],
    "servicios_por_categoria": [
      {
        "categoria__nombre": "Limpieza",
        "cantidad": 15
      }
    ],
    "turnos_por_estado": [
      {
        "estado": "completado",
        "cantidad": 250
      },
      {
        "estado": "confirmado",
        "cantidad": 50
      }
    ],
    "total_turnos": 350,
    "turnos_completados": 250,
    "tasa_completitud": 71.43,
    "periodo": {
      "inicio": "2025-10-05T00:00:00Z",
      "fin": "2025-11-05T00:00:00Z"
    }
  }
}
```

**Respuesta Exitosa (200 OK) - Ingresos:**
```json
{
  "success": true,
  "tipo": "ingresos",
  "data": {
    "ingresos_totales": 125000.00,
    "ingresos_por_mes": [
      {
        "mes": "2025-10-01T00:00:00Z",
        "total": 45000.00,
        "cantidad_turnos": 90
      }
    ],
    "ingresos_por_categoria": [
      {
        "categoria": "Limpieza",
        "total": 65000.00,
        "cantidad": 130
      }
    ],
    "ticket_promedio": 500.00,
    "profesionales_top": [
      {
        "profesional__usuario__username": "prof1",
        "profesional__usuario__first_name": "Juan",
        "profesional__usuario__last_name": "Pérez",
        "ingresos": 15000.00,
        "cantidad_turnos": 30
      }
    ],
    "periodo": {
      "inicio": "2025-10-05T00:00:00Z",
      "fin": "2025-11-05T00:00:00Z"
    }
  }
}
```

**Respuesta Exitosa (200 OK) - Calificaciones:**
```json
{
  "success": true,
  "tipo": "calificaciones",
  "data": {
    "calificacion_promedio": 4.65,
    "total_calificaciones": 245,
    "distribucion": [
      {
        "puntuacion": 5,
        "cantidad": 150
      },
      {
        "puntuacion": 4,
        "cantidad": 70
      }
    ],
    "por_servicio": [
      {
        "turno__servicio__nombre": "Limpieza General",
        "promedio": 4.8,
        "cantidad": 85
      }
    ],
    "profesionales_mejor": [
      {
        "turno__profesional__usuario__username": "prof1",
        "turno__profesional__usuario__first_name": "Juan",
        "turno__profesional__usuario__last_name": "Pérez",
        "promedio": 4.9,
        "cantidad": 50
      }
    ],
    "periodo": {
      "inicio": "2025-10-05T00:00:00Z",
      "fin": "2025-11-05T00:00:00Z"
    }
  }
}
```

**Respuesta de Error (400 Bad Request):**
```json
{
  "success": false,
  "message": "Parámetros inválidos",
  "errors": {
    "tipo": ["Este campo es requerido."],
    "fecha_inicio": ["Para período personalizado se requieren fecha_inicio y fecha_fin"]
  }
}
```

---

## 2. Reporte de Preferencias de Clientes (CU-31)

**Endpoint:** `GET /api/reportes/clientes/`

**Descripción:** Genera un reporte detallado sobre preferencias, patrones de uso y segmentación de clientes.

**Query Parameters:**
- `fecha_inicio` (datetime, opcional): Inicio del período de análisis (ISO 8601)
  - Default: hace 90 días
- `fecha_fin` (datetime, opcional): Fin del período de análisis (ISO 8601)
  - Default: hoy
- `guardar` (boolean, opcional): Si es `true`, guarda el reporte en la base de datos
  - Default: `false`

**Ejemplo:**
```bash
# Reporte del último trimestre (default)
GET /api/reportes/clientes/

# Reporte personalizado y guardado
GET /api/reportes/clientes/?fecha_inicio=2025-01-01T00:00:00Z&fecha_fin=2025-03-31T23:59:59Z&guardar=true
```

**Respuesta Exitosa (200 OK):**
```json
{
  "success": true,
  "message": "Reporte generado exitosamente",
  "reporte_id": 15,
  "data": {
    "tipo": "preferencias_clientes",
    "periodo": {
      "inicio": "2025-08-05T00:00:00Z",
      "fin": "2025-11-05T00:00:00Z"
    },
    "servicios_por_cliente": [
      {
        "cliente__usuario__username": "cliente1",
        "cliente__usuario__first_name": "María",
        "cliente__usuario__last_name": "García",
        "servicio__nombre": "Limpieza General",
        "servicio__categoria__nombre": "Limpieza",
        "cantidad": 8
      }
    ],
    "frecuencia_horaria": [
      {
        "hora_turno": 9,
        "cantidad": 45
      },
      {
        "hora_turno": 10,
        "cantidad": 62
      }
    ],
    "dias_semana_populares": [
      {
        "dia_semana": 1,
        "cantidad": 50
      },
      {
        "dia_semana": 5,
        "cantidad": 45
      }
    ],
    "tasa_cancelacion": 8.5,
    "clientes_frecuentes": [
      {
        "username": "cliente1",
        "nombre": "María García",
        "cantidad_turnos": 15,
        "gasto_total": 7500.00,
        "servicios_distintos": 3
      }
    ],
    "segmentacion": {
      "muy_activos": 12,
      "activos": 25,
      "ocasionales": 45,
      "nuevos": 30
    },
    "total_clientes_analizados": 112
  }
}
```

---

## 3. Reporte de Profesionales (CU-30)

**Endpoint:** `GET /api/reportes/profesionales/`

**Descripción:** Genera un reporte detallado sobre desempeño y estadísticas de profesionales.

**Query Parameters:**
- `fecha_inicio` (datetime, opcional): Inicio del período de análisis
  - Default: hace 90 días
- `fecha_fin` (datetime, opcional): Fin del período de análisis
  - Default: hoy
- `servicio_id` (integer, opcional): ID del servicio para filtrar
- `calificacion_min` (float, opcional): Calificación mínima (1.0 - 5.0)
- `antiguedad_min` (integer, opcional): Antigüedad mínima en días
- `guardar` (boolean, opcional): Si es `true`, guarda el reporte
  - Default: `false`

**Ejemplos:**
```bash
# Reporte general
GET /api/reportes/profesionales/

# Profesionales con calificación >= 4.5
GET /api/reportes/profesionales/?calificacion_min=4.5

# Profesionales de servicio específico con antigüedad
GET /api/reportes/profesionales/?servicio_id=3&antiguedad_min=180&guardar=true
```

**Respuesta Exitosa (200 OK):**
```json
{
  "success": true,
  "message": "Reporte generado exitosamente",
  "reporte_id": 16,
  "data": {
    "tipo": "profesionales",
    "periodo": {
      "inicio": "2025-08-05T00:00:00Z",
      "fin": "2025-11-05T00:00:00Z"
    },
    "filtros_aplicados": {
      "calificacion_min": 4.5,
      "servicio_id": 3
    },
    "resumen": {
      "total_profesionales": 15,
      "servicios_totales": 450,
      "ingresos_totales": 225000.00,
      "calificacion_promedio_general": 4.72
    },
    "profesionales": [
      {
        "id": 5,
        "username": "prof1",
        "nombre_completo": "Juan Pérez",
        "servicios_prestados": 50,
        "servicios_completados": 48,
        "calificacion_promedio": 4.9,
        "ingresos_generados": 24000.00,
        "tasa_completitud": 96.0,
        "antiguedad_dias": 365
      },
      {
        "id": 8,
        "username": "prof2",
        "nombre_completo": "Ana López",
        "servicios_prestados": 45,
        "servicios_completados": 42,
        "calificacion_promedio": 4.7,
        "ingresos_generados": 21000.00,
        "tasa_completitud": 93.33,
        "antiguedad_dias": 280
      }
    ]
  }
}
```

---

## 4. Búsqueda de Promociones (CU-40)

### Buscar Promociones

**Endpoint:** `GET /api/reportes/promociones/buscar/`

**Descripción:** Busca promociones por múltiples criterios con soporte de paginación.

**Query Parameters:**
- `nombre` (string, opcional): Texto a buscar en título, descripción o código
- `estado` (string, opcional): Estado de la promoción
  - Valores: `activa`, `inactiva`
- `fecha_inicio` (datetime, opcional): Inicio del rango de vigencia
- `fecha_fin` (datetime, opcional): Fin del rango de vigencia
- `page` (integer, opcional): Número de página
  - Default: 1
- `page_size` (integer, opcional): Tamaño de página
  - Default: 50, Max: 100

**Ejemplos:**
```bash
# Buscar por nombre
GET /api/reportes/promociones/buscar/?nombre=verano

# Buscar promociones activas
GET /api/reportes/promociones/buscar/?estado=activa

# Buscar por rango de fechas
GET /api/reportes/promociones/buscar/?fecha_inicio=2025-01-01T00:00:00Z&fecha_fin=2025-03-31T23:59:59Z

# Combinación de criterios con paginación
GET /api/reportes/promociones/buscar/?nombre=descuento&estado=activa&page=2&page_size=20
```

**Respuesta Exitosa (200 OK) - Con Paginación:**
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/reportes/promociones/buscar/?page=2",
  "previous": null,
  "success": true,
  "message": "45 promociones encontradas",
  "filtros_aplicados": {
    "nombre": "verano",
    "estado": "activa"
  },
  "results": [
    {
      "id": 1,
      "titulo": "Descuento de Verano 2025",
      "descripcion": "20% de descuento en todos los servicios de limpieza",
      "tipo_descuento": "porcentaje",
      "tipo_descuento_display": "Porcentaje",
      "valor_descuento": "20.00",
      "categoria_nombre": "Limpieza",
      "cantidad_servicios": 5,
      "fecha_inicio": "2025-01-01T00:00:00Z",
      "fecha_fin": "2025-03-31T23:59:59Z",
      "activa": true,
      "esta_vigente": false,
      "codigo": "VERANO2025",
      "fecha_creacion": "2024-12-15T10:00:00Z"
    }
  ]
}
```

---

### Detalle de Promoción

**Endpoint:** `GET /api/reportes/promociones/{id}/detalle/`

**Descripción:** Obtiene información completa de una promoción específica.

**Ejemplo:**
```bash
GET /api/reportes/promociones/1/detalle/
```

**Respuesta Exitosa (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "titulo": "Descuento de Verano 2025",
    "descripcion": "20% de descuento en todos los servicios de limpieza durante el verano",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "20.00",
    "categoria": 1,
    "categoria_detalle": {
      "id": 1,
      "nombre": "Limpieza"
    },
    "servicios": [1, 2, 3],
    "servicios_detalle": [
      {
        "id": 1,
        "nombre": "Limpieza General",
        "categoria_nombre": "Limpieza"
      },
      {
        "id": 2,
        "nombre": "Limpieza Profunda",
        "categoria_nombre": "Limpieza"
      }
    ],
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-03-31T23:59:59Z",
    "activa": true,
    "codigo": "VERANO2025",
    "fecha_creacion": "2024-12-15T10:00:00Z",
    "fecha_modificacion": "2024-12-15T10:00:00Z",
    "esta_vigente": false
  }
}
```

---

## 5. Gestión de Reportes Guardados

### Listar Reportes

**Endpoint:** `GET /api/reportes/`

**Descripción:** Lista todos los reportes guardados en el sistema.

**Query Parameters:**
- `tipo` (string, opcional): Filtrar por tipo de reporte
  - Valores: `preferencias_cliente`, `profesionales`, etc.
- `page` (integer, opcional): Número de página
- `page_size` (integer, opcional): Tamaño de página

**Ejemplo:**
```bash
# Listar todos los reportes
GET /api/reportes/

# Listar reportes de clientes
GET /api/reportes/?tipo=preferencias_cliente
```

**Respuesta Exitosa (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/reportes/?page=2",
  "previous": null,
  "success": true,
  "results": [
    {
      "id": 15,
      "tipo": "preferencias_cliente",
      "tipo_display": "Preferencias y Comportamientos de Cliente",
      "titulo": "Reporte de preferencias_cliente - 2025-11-05 14:30",
      "fecha_generacion": "2025-11-05T14:30:00Z",
      "generado_por_username": "admin"
    }
  ]
}
```

---

### Detalle de Reporte Guardado

**Endpoint:** `GET /api/reportes/{id}/`

**Descripción:** Obtiene los datos completos de un reporte guardado.

**Ejemplo:**
```bash
GET /api/reportes/15/
```

**Respuesta Exitosa (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 15,
    "tipo": "preferencias_cliente",
    "tipo_display": "Preferencias y Comportamientos de Cliente",
    "titulo": "Reporte de preferencias_cliente - 2025-11-05 14:30",
    "descripcion": null,
    "fecha_generacion": "2025-11-05T14:30:00Z",
    "generado_por_username": "admin",
    "datos_json": {
      "tipo": "preferencias_clientes",
      "periodo": {...},
      "servicios_por_cliente": [...],
      "clientes_frecuentes": [...]
    }
  }
}
```

---

## Códigos de Estado HTTP

- `200 OK`: Operación exitosa
- `400 Bad Request`: Error de validación en parámetros
- `401 Unauthorized`: Token inválido o no proporcionado
- `403 Forbidden`: Usuario no tiene permisos de administrador
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error en el servidor

---

## Seguridad y Permisos

### Autenticación
- ✅ JWT Bearer Token requerido en todos los endpoints
- ✅ Validación de token en cada request
- ✅ Usuario debe estar autenticado

### Autorización
- ✅ Solo administradores pueden acceder a todos los endpoints
- ✅ Validación de rol `administrador` en cada petición
- ✅ Logs de auditoría para todas las operaciones

### Logging y Auditoría
- ✅ Todos los endpoints registran logs informativos
- ✅ Errores detallados en logs del servidor
- ✅ Registro de usuario que realiza cada operación

---

## Escalabilidad

### Optimización de Queries
- ✅ Uso de `select_related` y `prefetch_related`
- ✅ Agregaciones a nivel de base de datos
- ✅ Índices en campos clave

### Paginación
- ✅ Paginación en búsqueda de promociones
- ✅ Límite de resultados configurable
- ✅ Máximo 100 items por página

### Caché (recomendado para producción)
- Estadísticas frecuentes pueden cachearse
- TTL sugerido: 5-15 minutos
- Invalidación al actualizar datos

---

## Ejemplos de Uso Completo

### Flujo 1: Análisis Mensual Completo
```bash
# 1. Estadísticas de usuarios
curl -X GET "http://localhost:8000/api/reportes/estadisticas/?tipo=usuarios&periodo=mes" \
  -H "Authorization: Bearer <token>"

# 2. Estadísticas de servicios
curl -X GET "http://localhost:8000/api/reportes/estadisticas/?tipo=servicios&periodo=mes" \
  -H "Authorization: Bearer <token>"

# 3. Estadísticas de ingresos
curl -X GET "http://localhost:8000/api/reportes/estadisticas/?tipo=ingresos&periodo=mes" \
  -H "Authorization: Bearer <token>"

# 4. Reporte de clientes (guardado)
curl -X GET "http://localhost:8000/api/reportes/clientes/?guardar=true" \
  -H "Authorization: Bearer <token>"

# 5. Reporte de profesionales (guardado)
curl -X GET "http://localhost:8000/api/reportes/profesionales/?guardar=true" \
  -H "Authorization: Bearer <token>"
```

### Flujo 2: Análisis de Promociones
```bash
# 1. Buscar promociones activas
curl -X GET "http://localhost:8000/api/reportes/promociones/buscar/?estado=activa" \
  -H "Authorization: Bearer <token>"

# 2. Obtener detalle de promoción específica
curl -X GET "http://localhost:8000/api/reportes/promociones/1/detalle/" \
  -H "Authorization: Bearer <token>"

# 3. Buscar promociones por rango de fechas
curl -X GET "http://localhost:8000/api/reportes/promociones/buscar/?fecha_inicio=2025-01-01T00:00:00Z&fecha_fin=2025-12-31T23:59:59Z" \
  -H "Authorization: Bearer <token>"
```

---

## Manejo de Errores

### Error de Autenticación
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Error de Permisos
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Error de Validación
```json
{
  "success": false,
  "message": "Parámetros inválidos",
  "errors": {
    "tipo": ["Este campo es requerido."],
    "periodo": ["'invalid' no es una opción válida."]
  }
}
```

### Error del Servidor
```json
{
  "success": false,
  "message": "Error al consultar estadísticas. Por favor, intente nuevamente."
}
```

---

## Notas de Implementación

### Consideraciones de Performance
1. **Consultas pesadas**: Las estadísticas e ingresos pueden ser costosas en grandes volúmenes
2. **Recomendación**: Implementar caché para consultas frecuentes
3. **Índices**: Asegurar índices en: `fecha_solicitud`, `estado`, `fecha_inicio`, `fecha_fin`

### Formatos de Fecha
- Todas las fechas deben estar en formato ISO 8601
- Incluir timezone (preferiblemente UTC)
- Ejemplo: `2025-01-01T00:00:00Z`

### Límites y Cuotas
- Máximo 100 items por página en búsquedas paginadas
- Reportes guardados tienen límite de espacio JSON
- Considerar limpieza periódica de reportes antiguos

---

**Versión:** 1.0  
**Fecha:** Noviembre 2025  
**Framework:** Django REST Framework 3.14.0
