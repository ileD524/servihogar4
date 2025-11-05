# Guía de Pruebas Prácticas - API Promociones

## 🚀 Inicio Rápido

### 1. Iniciar el Servidor
```bash
venv\Scripts\python.exe manage.py runserver
```

### 2. Obtener Token JWT de Administrador
Primero necesitas autenticarte como administrador. Si no tienes uno, créalo:

```bash
venv\Scripts\python.exe manage.py createsuperuser
# Asegúrate de que el usuario tenga rol='administrador'
```

O usa el endpoint de login (si está implementado):
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "tu_password"
  }'
```

**Respuesta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Guarda el `access` token para las siguientes peticiones.

---

## 📝 Pruebas de CU-18: Registrar Promoción

### ✅ Caso 1: Registro Exitoso (Porcentaje)

```bash
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Descuento Verano 2025",
    "descripcion": "20% de descuento en todos los servicios de limpieza",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "20.00",
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-03-31T23:59:59Z",
    "codigo": "VERANO2025"
  }'
```

**Resultado esperado:** ✅ 201 Created

### ✅ Caso 2: Registro Exitoso (Monto Fijo)

```bash
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Black Friday 2025",
    "descripcion": "$500 de descuento en servicios seleccionados",
    "tipo_descuento": "monto_fijo",
    "valor_descuento": "500.00",
    "fecha_inicio": "2025-11-29T00:00:00Z",
    "fecha_fin": "2025-11-29T23:59:59Z",
    "codigo": "BLACKFRIDAY"
  }'
```

**Resultado esperado:** ✅ 201 Created

### ❌ Caso 3: Error - Fechas Incoherentes

```bash
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Promo Error Fechas",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "10.00",
    "fecha_inicio": "2025-12-31T23:59:59Z",
    "fecha_fin": "2025-01-01T00:00:00Z"
  }'
```

**Resultado esperado:** ❌ 400 Bad Request
```json
{
  "success": false,
  "message": "Error en validación de reglas de negocio",
  "errors": {
    "fechas": "La fecha de inicio debe ser anterior o igual a la fecha de fin"
  }
}
```

### ❌ Caso 4: Error - Porcentaje Mayor a 100%

```bash
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Promo Error Porcentaje",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "150.00",
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-12-31T23:59:59Z"
  }'
```

**Resultado esperado:** ❌ 400 Bad Request
```json
{
  "errors": {
    "valor_descuento": "El porcentaje no puede superar el 100.00%"
  }
}
```

### ❌ Caso 5: Error - Nombre Duplicado

```bash
# Primera promoción (exitosa)
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Promo Única",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "10.00",
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-01-31T23:59:59Z"
  }'

# Segunda con mismo nombre (error)
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Promo Única",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "15.00",
    "fecha_inicio": "2025-02-01T00:00:00Z",
    "fecha_fin": "2025-02-28T23:59:59Z"
  }'
```

**Resultado esperado:** ❌ 400 Bad Request
```json
{
  "errors": {
    "titulo": "Ya existe una promoción con el nombre 'Promo Única'"
  }
}
```

---

## 📋 Pruebas de Listados

### Listar Todas las Promociones

```bash
curl -X GET http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

### Listar Solo Promociones Activas

```bash
curl -X GET "http://localhost:8000/api/promociones/?activa=true" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

### Listar Promociones Vigentes (Sin Autenticación)

```bash
curl -X GET http://localhost:8000/api/promociones/vigentes/
```

**Este endpoint es público, no requiere token.**

---

## 🔍 Pruebas de Detalle

### Obtener Detalle de Promoción

```bash
curl -X GET http://localhost:8000/api/promociones/1/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

Reemplaza `1` con el ID de la promoción que quieres consultar.

---

## ✏️ Pruebas de CU-19: Modificar Promoción

### ✅ Caso 1: Modificación Exitosa (Un Campo)

```bash
curl -X PUT http://localhost:8000/api/promociones/1/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "valor_descuento": "25.00"
  }'
```

**Resultado esperado:** ✅ 200 OK

### ✅ Caso 2: Modificación Exitosa (Múltiples Campos)

```bash
curl -X PUT http://localhost:8000/api/promociones/1/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Descuento Verano 2025 - Actualizado",
    "descripcion": "Nueva descripción mejorada",
    "valor_descuento": "30.00",
    "fecha_fin": "2025-04-30T23:59:59Z"
  }'
```

**Resultado esperado:** ✅ 200 OK

### ❌ Caso 3: Error - Nombre Duplicado en Modificación

```bash
# Asumiendo que existe "Black Friday 2025" con ID 2
curl -X PUT http://localhost:8000/api/promociones/1/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Black Friday 2025"
  }'
```

**Resultado esperado:** ❌ 400 Bad Request
```json
{
  "errors": {
    "titulo": "Ya existe una promoción con el nombre 'Black Friday 2025'"
  }
}
```

---

## 🗑️ Pruebas de CU-20: Eliminar Promoción

### Paso 1: Validar si Puede Eliminarse

```bash
curl -X GET http://localhost:8000/api/promociones/1/validar-eliminacion/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

**Respuesta si puede eliminarse:**
```json
{
  "success": true,
  "puede_eliminar": true,
  "message": "La promoción puede eliminarse",
  "turnos_activos": 0
}
```

**Respuesta si NO puede eliminarse:**
```json
{
  "success": true,
  "puede_eliminar": false,
  "message": "No se puede eliminar la promoción porque tiene 3 turno(s) activo(s) asociado(s)",
  "turnos_activos": 3
}
```

### ✅ Caso 1: Eliminación Exitosa (Sin Turnos Activos)

```bash
curl -X DELETE http://localhost:8000/api/promociones/1/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

**Resultado esperado:** ✅ 200 OK
```json
{
  "success": true,
  "message": "Promoción eliminada exitosamente"
}
```

### ❌ Caso 2: Error - Promoción con Turnos Activos

Para probar este caso, primero necesitas:
1. Crear una promoción
2. Asociarla a un turno en estado "pendiente", "confirmado" o "en_curso"
3. Intentar eliminarla

```bash
curl -X DELETE http://localhost:8000/api/promociones/2/ \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

**Resultado esperado:** ❌ 400 Bad Request
```json
{
  "success": false,
  "message": "No se puede eliminar la promoción porque tiene 5 turno(s) activo(s) asociado(s)"
}
```

---

## 🔒 Pruebas de Seguridad

### ❌ Sin Autenticación

```bash
curl -X GET http://localhost:8000/api/promociones/
```

**Resultado esperado:** ❌ 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### ❌ Con Usuario No Administrador

Si tienes un token de un usuario cliente o profesional:

```bash
curl -X POST http://localhost:8000/api/promociones/ \
  -H "Authorization: Bearer TOKEN_NO_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Test",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "10.00",
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-12-31T23:59:59Z"
  }'
```

**Resultado esperado:** ❌ 403 Forbidden

---

## 🧪 Script de Prueba Completo (Python)

Si prefieres usar Python para probar:

```python
import requests
import json

# Configuración
BASE_URL = "http://localhost:8000/api"
TOKEN = "tu_token_jwt_aqui"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. Registrar promoción
print("1. Registrando promoción...")
data = {
    "titulo": "Promoción de Prueba",
    "descripcion": "Descripción de prueba",
    "tipo_descuento": "porcentaje",
    "valor_descuento": "15.00",
    "fecha_inicio": "2025-01-01T00:00:00Z",
    "fecha_fin": "2025-12-31T23:59:59Z",
    "codigo": "TEST2025"
}
response = requests.post(f"{BASE_URL}/promociones/", json=data, headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Guardar ID de la promoción
promocion_id = response.json()['data']['id']

# 2. Listar promociones
print("\n2. Listando promociones...")
response = requests.get(f"{BASE_URL}/promociones/", headers=headers)
print(f"Status: {response.status_code}")
print(f"Total: {response.json()['count']}")

# 3. Obtener detalle
print(f"\n3. Obteniendo detalle de promoción {promocion_id}...")
response = requests.get(f"{BASE_URL}/promociones/{promocion_id}/", headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# 4. Modificar promoción
print(f"\n4. Modificando promoción {promocion_id}...")
data = {"valor_descuento": "20.00"}
response = requests.put(f"{BASE_URL}/promociones/{promocion_id}/", json=data, headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# 5. Validar eliminación
print(f"\n5. Validando eliminación de promoción {promocion_id}...")
response = requests.get(f"{BASE_URL}/promociones/{promocion_id}/validar-eliminacion/", headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# 6. Eliminar promoción
print(f"\n6. Eliminando promoción {promocion_id}...")
response = requests.delete(f"{BASE_URL}/promociones/{promocion_id}/", headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# 7. Listar promociones vigentes (público)
print("\n7. Listando promociones vigentes (público)...")
response = requests.get(f"{BASE_URL}/promociones/vigentes/")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
```

---

## 📊 Checklist de Pruebas

### CU-18: Registrar Promoción
- [ ] ✅ Registro con tipo porcentaje
- [ ] ✅ Registro con tipo monto fijo
- [ ] ✅ Registro con categoría
- [ ] ✅ Registro con servicios
- [ ] ❌ Error por fechas incoherentes
- [ ] ❌ Error por porcentaje > 100%
- [ ] ❌ Error por monto negativo
- [ ] ❌ Error por nombre duplicado
- [ ] ❌ Error por promoción solapada

### CU-19: Modificar Promoción
- [ ] ✅ Modificar un campo
- [ ] ✅ Modificar múltiples campos
- [ ] ✅ Modificar fechas
- [ ] ✅ Modificar valor de descuento
- [ ] ❌ Error por nombre duplicado
- [ ] ❌ Error por validaciones de CU-18

### CU-20: Eliminar Promoción
- [ ] ✅ Validar eliminación sin turnos
- [ ] ✅ Eliminar sin turnos activos
- [ ] ❌ Error por turnos activos
- [ ] ✅ Verificar soft delete (activa=False)

### Seguridad
- [ ] ❌ Sin autenticación (401)
- [ ] ❌ Con usuario no admin (403)
- [ ] ✅ Con usuario admin (200/201)

### Listados
- [ ] ✅ Listar todas
- [ ] ✅ Filtrar por activa
- [ ] ✅ Filtrar por vigente
- [ ] ✅ Promociones vigentes (público)

---

## 💡 Consejos

1. **Orden de pruebas:** Ejecuta primero los casos exitosos y luego los de error
2. **IDs dinámicos:** Los IDs cambiarán, ajusta según tus datos
3. **Fechas:** Usa fechas futuras para que las promociones sean vigentes
4. **Tokens:** El token JWT expira, genera uno nuevo si es necesario
5. **Base de datos:** Considera usar la base de datos de prueba para no afectar producción

---

## 🐛 Troubleshooting

### Error: "Authentication credentials were not provided"
**Solución:** Verifica que estás incluyendo el header `Authorization: Bearer <token>`

### Error: 403 Forbidden
**Solución:** El usuario debe tener `rol='administrador'`

### Error: 404 Not Found
**Solución:** Verifica que la URL sea correcta y que el ID exista

### Error: 500 Internal Server Error
**Solución:** Revisa los logs del servidor con `python manage.py runserver`

---

**¡Buena suerte con las pruebas!** 🚀
