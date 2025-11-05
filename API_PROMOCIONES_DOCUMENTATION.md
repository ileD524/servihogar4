# API REST - Gestión de Promociones

## Descripción General

Esta API REST implementa los endpoints para la gestión de promociones (CU-18, CU-19, CU-20) en el sistema de reservas de servicios ServiHogar. Todos los endpoints requieren autenticación como **Administrador** excepto el endpoint público de promociones vigentes.

## Autenticación

Todas las operaciones (excepto GET /api/promociones/vigentes/) requieren:
- Token JWT en el header: `Authorization: Bearer <token>`
- Usuario con rol `administrador`

## Endpoints

### 1. Registrar Promoción (CU-18)

Permite registrar una nueva promoción con todas las validaciones de negocio.

**Endpoint:** `POST /api/promociones/`

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "titulo": "Promoción de Verano 2025",
    "descripcion": "Descuento especial en servicios de limpieza durante el verano",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "15.00",
    "categoria": 1,
    "servicios": [1, 2, 3],
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-01-31T23:59:59Z",
    "codigo": "VERANO2025"
}
```

**Campos:**
- `titulo` (string, requerido): Nombre de la promoción
- `descripcion` (string, opcional): Descripción detallada
- `tipo_descuento` (string, requerido): "porcentaje" o "monto_fijo"
- `valor_descuento` (decimal, requerido): Valor del descuento
  - Si es porcentaje: entre 0.01 y 100.00
  - Si es monto fijo: entre 0.01 y 999999.99
- `categoria` (integer, opcional): ID de la categoría a la que aplica
- `servicios` (array, opcional): IDs de los servicios a los que aplica
- `fecha_inicio` (datetime, requerido): Fecha de inicio de vigencia
- `fecha_fin` (datetime, requerido): Fecha de fin de vigencia
- `codigo` (string, opcional): Código promocional único

**Validaciones:**
1. Las fechas de inicio y fin deben ser coherentes (inicio <= fin)
2. El valor del descuento debe estar en el rango permitido
3. No deben existir promociones activas solapadas para el mismo período y condiciones
4. El título debe ser único en el sistema

**Respuesta Exitosa (201 Created):**
```json
{
    "success": true,
    "message": "Promoción registrada exitosamente",
    "data": {
        "id": 1,
        "titulo": "Promoción de Verano 2025",
        "descripcion": "Descuento especial en servicios de limpieza durante el verano",
        "tipo_descuento": "porcentaje",
        "valor_descuento": "15.00",
        "categoria": 1,
        "categoria_detalle": {
            "id": 1,
            "nombre": "Limpieza"
        },
        "servicios": [1, 2, 3],
        "servicios_detalle": [
            {
                "id": 1,
                "nombre": "Limpieza general",
                "categoria_nombre": "Limpieza"
            },
            {
                "id": 2,
                "nombre": "Limpieza profunda",
                "categoria_nombre": "Limpieza"
            }
        ],
        "fecha_inicio": "2025-01-01T00:00:00Z",
        "fecha_fin": "2025-01-31T23:59:59Z",
        "activa": true,
        "codigo": "VERANO2025",
        "fecha_creacion": "2025-11-05T10:30:00Z",
        "fecha_modificacion": "2025-11-05T10:30:00Z",
        "esta_vigente": false
    }
}
```

**Respuesta de Error (400 Bad Request):**
```json
{
    "success": false,
    "message": "Error en validación de reglas de negocio",
    "errors": {
        "fechas": "La fecha de inicio debe ser anterior o igual a la fecha de fin",
        "valor_descuento": "El porcentaje no puede superar el 100.00%",
        "solape": "Ya existe una promoción activa 'Promo Otoño' para la categoría 'Limpieza' en el período indicado",
        "titulo": "Ya existe una promoción con el nombre 'Promoción de Verano 2025'"
    }
}
```

---

### 2. Listar Promociones

Obtiene el listado de todas las promociones con filtros opcionales.

**Endpoint:** `GET /api/promociones/`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters (opcionales):**
- `activa` (boolean): Filtrar por estado activo (true/false)
- `vigente` (boolean): Filtrar solo promociones vigentes actualmente (true/false)

**Ejemplos:**
```
GET /api/promociones/
GET /api/promociones/?activa=true
GET /api/promociones/?vigente=true
```

**Respuesta Exitosa (200 OK):**
```json
{
    "success": true,
    "count": 5,
    "data": [
        {
            "id": 1,
            "titulo": "Promoción de Verano 2025",
            "tipo_descuento": "porcentaje",
            "tipo_descuento_display": "Porcentaje",
            "valor_descuento": "15.00",
            "categoria_nombre": "Limpieza",
            "cantidad_servicios": 2,
            "fecha_inicio": "2025-01-01T00:00:00Z",
            "fecha_fin": "2025-01-31T23:59:59Z",
            "activa": true,
            "esta_vigente": false,
            "fecha_creacion": "2025-11-05T10:30:00Z"
        },
        {
            "id": 2,
            "titulo": "Black Friday 2025",
            "tipo_descuento": "monto_fijo",
            "tipo_descuento_display": "Monto Fijo",
            "valor_descuento": "500.00",
            "categoria_nombre": null,
            "cantidad_servicios": 10,
            "fecha_inicio": "2025-11-29T00:00:00Z",
            "fecha_fin": "2025-11-29T23:59:59Z",
            "activa": true,
            "esta_vigente": true,
            "fecha_creacion": "2025-10-15T08:00:00Z"
        }
    ]
}
```

---

### 3. Obtener Detalle de Promoción

Obtiene la información detallada de una promoción específica.

**Endpoint:** `GET /api/promociones/{id}/`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Respuesta Exitosa (200 OK):**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "titulo": "Promoción de Verano 2025",
        "descripcion": "Descuento especial en servicios de limpieza durante el verano",
        "tipo_descuento": "porcentaje",
        "valor_descuento": "15.00",
        "categoria": 1,
        "categoria_detalle": {
            "id": 1,
            "nombre": "Limpieza"
        },
        "servicios": [1, 2],
        "servicios_detalle": [
            {
                "id": 1,
                "nombre": "Limpieza general",
                "categoria_nombre": "Limpieza"
            }
        ],
        "fecha_inicio": "2025-01-01T00:00:00Z",
        "fecha_fin": "2025-01-31T23:59:59Z",
        "activa": true,
        "codigo": "VERANO2025",
        "fecha_creacion": "2025-11-05T10:30:00Z",
        "fecha_modificacion": "2025-11-05T10:30:00Z",
        "esta_vigente": false
    }
}
```

**Respuesta de Error (404 Not Found):**
```json
{
    "detail": "Not found."
}
```

---

### 4. Modificar Promoción (CU-19)

Permite modificar cualquier promoción registrada aplicando todas las validaciones.

**Endpoint:** `PUT /api/promociones/{id}/`

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Body (JSON):** Todos los campos son opcionales, solo se envían los que se quieren modificar
```json
{
    "titulo": "Promoción de Verano 2025 - Actualizada",
    "descripcion": "Nueva descripción",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "20.00",
    "categoria": 2,
    "servicios": [3, 4, 5],
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-02-28T23:59:59Z",
    "codigo": "VERANO2025"
}
```

**Validaciones:**
1. Todas las validaciones de CU-18 (fechas, valor, solapamiento)
2. El nombre no debe duplicar otra promoción existente (excepto la misma)
3. Se registra automáticamente la fecha/hora de modificación

**Respuesta Exitosa (200 OK):**
```json
{
    "success": true,
    "message": "Promoción modificada exitosamente",
    "data": {
        "id": 1,
        "titulo": "Promoción de Verano 2025 - Actualizada",
        "descripcion": "Nueva descripción",
        "tipo_descuento": "porcentaje",
        "valor_descuento": "20.00",
        "categoria": 2,
        "categoria_detalle": {
            "id": 2,
            "nombre": "Plomería"
        },
        "servicios": [3, 4, 5],
        "servicios_detalle": [...],
        "fecha_inicio": "2025-01-01T00:00:00Z",
        "fecha_fin": "2025-02-28T23:59:59Z",
        "activa": true,
        "codigo": "VERANO2025",
        "fecha_creacion": "2025-11-05T10:30:00Z",
        "fecha_modificacion": "2025-11-05T15:45:00Z",
        "esta_vigente": false
    }
}
```

**Respuesta de Error (400 Bad Request):**
```json
{
    "success": false,
    "message": "Error en validación de reglas de negocio",
    "errors": {
        "titulo": "Ya existe una promoción con el nombre 'Promoción de Verano 2025 - Actualizada'",
        "solape": "Ya existe una promoción activa 'Promo Invierno' para el servicio 'Plomería' en el período indicado"
    }
}
```

---

### 5. Eliminar Promoción (CU-20)

Elimina (inactiva) una promoción. Solo puede eliminarse si no hay turnos activos asociados.

**Endpoint:** `DELETE /api/promociones/{id}/`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Validaciones:**
1. Solo puede eliminarse si no hay turnos activos (pendiente, confirmado, en_curso) asociados
2. La eliminación es lógica (soft delete): cambia `activa=False`
3. La promoción deja de estar disponible para nuevas reservas

**Respuesta Exitosa (200 OK):**
```json
{
    "success": true,
    "message": "Promoción eliminada exitosamente"
}
```

**Respuesta de Error - Turnos Activos (400 Bad Request):**
```json
{
    "success": false,
    "message": "No se puede eliminar la promoción porque tiene 3 turno(s) activo(s) asociado(s)"
}
```

**Respuesta de Error (404 Not Found):**
```json
{
    "detail": "Not found."
}
```

---

### 6. Validar si Puede Eliminarse

Verifica si una promoción puede ser eliminada sin intentar eliminarla.

**Endpoint:** `GET /api/promociones/{id}/validar-eliminacion/`

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Respuesta Exitosa (200 OK):**
```json
{
    "success": true,
    "puede_eliminar": true,
    "message": "La promoción puede eliminarse",
    "turnos_activos": 0
}
```

**Respuesta con Turnos Activos (200 OK):**
```json
{
    "success": true,
    "puede_eliminar": false,
    "message": "No se puede eliminar la promoción porque tiene 5 turno(s) activo(s) asociado(s)",
    "turnos_activos": 5
}
```

---

### 7. Listar Promociones Vigentes (Público)

Obtiene las promociones activas y vigentes en el momento actual. **No requiere autenticación**.

**Endpoint:** `GET /api/promociones/vigentes/`

**Headers:** No requiere autenticación

**Respuesta Exitosa (200 OK):**
```json
{
    "success": true,
    "count": 2,
    "data": [
        {
            "id": 2,
            "titulo": "Black Friday 2025",
            "tipo_descuento": "monto_fijo",
            "tipo_descuento_display": "Monto Fijo",
            "valor_descuento": "500.00",
            "categoria_nombre": null,
            "cantidad_servicios": 10,
            "fecha_inicio": "2025-11-29T00:00:00Z",
            "fecha_fin": "2025-11-29T23:59:59Z",
            "activa": true,
            "esta_vigente": true,
            "fecha_creacion": "2025-10-15T08:00:00Z"
        }
    ]
}
```

---

## Códigos de Estado HTTP

- `200 OK`: Operación exitosa (GET, DELETE)
- `201 Created`: Promoción creada exitosamente (POST)
- `400 Bad Request`: Error de validación o reglas de negocio
- `401 Unauthorized`: Token inválido o no proporcionado
- `403 Forbidden`: Usuario no tiene permisos (no es administrador)
- `404 Not Found`: Promoción no encontrada

---

## Reglas de Negocio Implementadas

### Validaciones de Fechas
- La fecha de inicio debe ser anterior o igual a la fecha de fin
- Ambas fechas son obligatorias

### Validaciones de Descuento
- **Porcentaje:**
  - Mínimo: 0.01%
  - Máximo: 100.00%
- **Monto Fijo:**
  - Mínimo: $0.01
  - Máximo: $999,999.99

### Validación de Solapamiento
Dos promociones se solapan si:
- Sus períodos de vigencia se superponen
- Aplican a las mismas categorías o servicios

### Validación de Nombre Único
- No pueden existir dos promociones con el mismo título (case-insensitive)
- Al modificar, se permite mantener el mismo nombre

### Validación de Eliminación
- Solo puede eliminarse si no hay turnos en estado:
  - `pendiente`
  - `confirmado`
  - `en_curso`
- Los turnos `completado` o `cancelado` no bloquean la eliminación

---

## Arquitectura

### Capa de Servicio (services.py)
Contiene toda la lógica de negocio:
- `PromocionService.registrar_promocion()`
- `PromocionService.modificar_promocion()`
- `PromocionService.eliminar_promocion()`
- `PromocionService.validar_fechas()`
- `PromocionService.validar_valor_descuento()`
- `PromocionService.validar_promociones_solapadas()`
- `PromocionService.validar_nombre_unico()`
- `PromocionService.puede_eliminar_promocion()`

### Capa de Controlador (api_views.py)
Maneja las peticiones HTTP:
- `PromocionListCreateAPIView` (GET, POST)
- `PromocionDetailAPIView` (GET, PUT, DELETE)
- `PromocionValidarEliminacionAPIView` (GET)
- `PromocionVigentesAPIView` (GET público)

### Capa de Modelo (models.py)
Define la estructura de datos:
- `Promocion` con todos sus campos y relaciones

### Serializers (serializers.py)
Maneja la serialización/deserialización:
- `PromocionSerializer` (detalle completo)
- `PromocionListSerializer` (listados)
- `PromocionCreateUpdateSerializer` (crear/modificar)

---

## Ejemplos de Uso

### Ejemplo 1: Registrar promoción de porcentaje

```bash
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Descuento Primavera",
    "descripcion": "20% de descuento en todos los servicios",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "20.00",
    "fecha_inicio": "2025-09-21T00:00:00Z",
    "fecha_fin": "2025-12-21T23:59:59Z"
  }'
```

### Ejemplo 2: Modificar valor de descuento

```bash
curl -X PUT http://localhost:8000/api/promociones/1/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "valor_descuento": "25.00"
  }'
```

### Ejemplo 3: Verificar si puede eliminarse

```bash
curl -X GET http://localhost:8000/api/promociones/1/validar-eliminacion/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Ejemplo 4: Eliminar promoción

```bash
curl -X DELETE http://localhost:8000/api/promociones/1/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Ejemplo 5: Listar promociones vigentes (sin autenticación)

```bash
curl -X GET http://localhost:8000/api/promociones/vigentes/
```

---

## Testing

### Escenarios de Prueba Recomendados

1. **Registro exitoso de promoción**
2. **Error por fechas incoherentes**
3. **Error por valor de descuento fuera de rango**
4. **Error por solapamiento de promociones**
5. **Error por nombre duplicado**
6. **Modificación exitosa**
7. **Eliminación exitosa sin turnos**
8. **Error al eliminar con turnos activos**
9. **Listado con filtros**
10. **Acceso sin autenticación (debe fallar)**
11. **Acceso con rol no administrador (debe fallar)**

---

## Notas Importantes

1. Todas las fechas deben estar en formato ISO 8601 con timezone UTC
2. Los valores decimales usan punto como separador (15.00, no 15,00)
3. La eliminación es lógica (soft delete), no física
4. El campo `fecha_modificacion` se actualiza automáticamente
5. Una promoción puede aplicar a una categoría O a servicios específicos
6. El endpoint de promociones vigentes es público para que los clientes puedan consultarlo

---

## Versión de la API

**Versión:** 1.0  
**Fecha:** Noviembre 2025  
**Framework:** Django REST Framework
