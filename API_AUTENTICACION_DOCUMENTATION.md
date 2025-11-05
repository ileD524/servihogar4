# API de Autenticación - ServiHogar

## Resumen Ejecutivo

Esta documentación describe la implementación completa de los casos de uso **CU-07 (Iniciar Sesión)** y **CU-08 (Cerrar Sesión)** para el sistema ServiHogar.

La implementación sigue arquitectura REST con autenticación JWT (JSON Web Tokens) y soporte para:
- ✅ **Login con email/contraseña**
- ✅ **Login con Google OAuth**
- ✅ **Cierre de sesión seguro**
- ✅ **Protección contra fuerza bruta**
- ✅ **Gestión de tokens JWT**
- ✅ **Blacklist de tokens**

---

## 📋 Tabla de Contenidos

1. [Casos de Uso Implementados](#casos-de-uso-implementados)
2. [Arquitectura](#arquitectura)
3. [Endpoints API](#endpoints-api)
4. [Seguridad](#seguridad)
5. [Flujos de Autenticación](#flujos-de-autenticación)
6. [Tokens JWT](#tokens-jwt)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Testing](#testing)
9. [Rate Limiting](#rate-limiting)
10. [Troubleshooting](#troubleshooting)

---

## Casos de Uso Implementados

### CU-07: Iniciar Sesión

**Actores**: Cliente, Profesional, Administrador (cualquier tipo de usuario)

**Descripción**: Permite iniciar sesión en el sistema usando dos métodos:

#### Método 1: Email y Contraseña
- Usuario proporciona email y contraseña
- Sistema valida credenciales contra la base de datos
- Sistema verifica que el usuario esté activo
- Sistema genera tokens JWT (access + refresh)
- Sistema registra el acceso y actualiza último login

#### Método 2: Google OAuth
- Frontend obtiene token de Google OAuth
- Backend valida token con Google API
- Sistema verifica email verificado
- Sistema busca o vincula usuario existente
- Sistema genera tokens JWT propios
- Sistema registra el acceso

**Seguridad**:
- ✅ Protección contra fuerza bruta (rate limiting)
- ✅ Bloqueo temporal tras 5 intentos fallidos (15 minutos)
- ✅ No revela qué dato es incorrecto (email o password)
- ✅ Logging completo de todos los intentos
- ✅ Validación directa con Google API (no confianza ciega)

**Archivo**: `apps/usuarios/auth_services.py` → `AuthService.login_email_password()` y `AuthService.login_google()`

---

### CU-08: Cerrar Sesión

**Actores**: Usuario autenticado (cualquier rol)

**Descripción**: Cierra la sesión del usuario de forma segura.

**Proceso**:
1. Django guarda automáticamente datos de sesión
2. Sistema invalida refresh token (blacklist)
3. Sistema destruye sesión de Django
4. Sistema registra el cierre de sesión

**Características**:
- ✅ Invalidación inmediata del refresh token
- ✅ Destrucción de sesión Django
- ✅ Access token sigue válido hasta expirar (60 min por defecto)
- ✅ Operación atómica (no deja sesiones huérfanas)
- ✅ Logging de todos los logouts

**Archivo**: `apps/usuarios/auth_services.py` → `AuthService.logout_user()`

---

## Arquitectura

### Estructura de Archivos

```
apps/usuarios/
├── auth_services.py           # Lógica de negocio de autenticación
├── auth_api_views.py          # Endpoints REST de autenticación
├── auth_urls.py               # Rutas de autenticación
├── serializers.py             # Serializers (ampliado)
├── tests_auth_services.py     # Tests de autenticación
└── models.py                  # Modelo Usuario (existente)

servihogar/
├── settings.py                # Configuración JWT (actualizado)
└── urls.py                    # URLs principales (actualizado)

requirements.txt               # Dependencias (actualizado)
```

### Flujo de Request

```
Cliente HTTP
    ↓
[auth_api_views.py] - Endpoint REST
    ↓
[serializers.py] - Validación de entrada
    ↓
[auth_services.py] - Lógica de autenticación
    ↓
[models.py] - Base de datos
    ↓
[JWT Token] - Generación de tokens
    ↓
Response con tokens
```

### Tecnologías Utilizadas

- **Django 5.2.7**: Framework web
- **Django REST Framework 3.14.0**: API REST
- **djangorestframework-simplejwt 5.3.1**: Autenticación JWT
- **google-auth 2.35.0**: Validación de tokens de Google OAuth

---

## Endpoints API

### Base URL

Todos los endpoints de autenticación están bajo:
```
/api/auth/
```

**Nota**: Estos endpoints son de acceso público (no requieren autenticación previa)

---

### 1. Login con Email y Contraseña

**Endpoint**: `POST /api/auth/login/`

**Descripción**: Inicia sesión usando email y contraseña.

**Permisos**: Acceso público

**Body Parameters**:
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `email` | string | Sí | Email registrado en el sistema |
| `password` | string | Sí | Contraseña de la cuenta |

**Ejemplo de Request**:
```json
{
  "email": "juan@ejemplo.com",
  "password": "MiPassword123!"
}
```

**Ejemplo de Response Exitosa** (200 OK):
```json
{
  "success": true,
  "message": "Inicio de sesión exitoso",
  "data": {
    "usuario": {
      "id": 5,
      "username": "juan_perez",
      "email": "juan@ejemplo.com",
      "first_name": "Juan",
      "last_name": "Pérez",
      "rol": "profesional",
      "foto_perfil": "/media/usuarios/juan.jpg"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

**Errores Comunes**:

```json
// 400 Bad Request - Credenciales inválidas
{
  "success": false,
  "error": "Credenciales inválidas"
}

// 403 Forbidden - Usuario bloqueado
{
  "success": false,
  "error": "Demasiados intentos fallidos. Cuenta bloqueada temporalmente. Intente nuevamente en 15 minutos."
}

// 400 Bad Request - Usuario desactivado
{
  "success": false,
  "error": "Esta cuenta está desactivada. Contacte al administrador para más información."
}
```

**Seguridad**:
- Máximo 5 intentos fallidos
- Bloqueo temporal de 15 minutos
- No revela si el error es en email o password

---

### 2. Login con Google OAuth

**Endpoint**: `POST /api/auth/login/google/`

**Descripción**: Inicia sesión usando token de Google OAuth.

**Permisos**: Acceso público

**Body Parameters**:
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `token` | string | Sí | Token JWT de Google OAuth obtenido desde frontend |

**Ejemplo de Request**:
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcifQ.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXpwIjoiNjM3..."
}
```

**Ejemplo de Response Exitosa** (200 OK):
```json
{
  "success": true,
  "message": "Inicio de sesión exitoso con Google",
  "data": {
    "usuario": {
      "id": 8,
      "username": "maria_garcia",
      "email": "maria@gmail.com",
      "first_name": "María",
      "last_name": "García",
      "rol": "cliente",
      "foto_perfil": "https://lh3.googleusercontent.com/a/..."
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

**Errores Comunes**:

```json
// 400 Bad Request - Token inválido
{
  "success": false,
  "error": "Token de Google inválido o expirado. Por favor, intente iniciar sesión nuevamente."
}

// 400 Bad Request - Email no verificado
{
  "success": false,
  "error": "El email de Google no está verificado. Por favor, verifique su cuenta de Google."
}

// 400 Bad Request - Usuario no registrado
{
  "success": false,
  "error": "Usuario no registrado. Por favor, complete el registro primero."
}
```

**Flujo Completo**:

1. **Frontend**: Integrar Google Sign-In Button
```javascript
// Frontend (React/Vue/Angular)
<GoogleLogin
  clientId="TU_GOOGLE_CLIENT_ID"
  onSuccess={handleGoogleSuccess}
  onFailure={handleGoogleFailure}
/>
```

2. **Frontend**: Enviar token al backend
```javascript
const handleGoogleSuccess = async (response) => {
  const tokenId = response.tokenId;
  
  const result = await fetch('/api/auth/login/google/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: tokenId })
  });
  
  const data = await result.json();
  // Guardar tokens en localStorage
  localStorage.setItem('access_token', data.data.tokens.access);
  localStorage.setItem('refresh_token', data.data.tokens.refresh);
};
```

3. **Backend**: Validar con Google API y generar tokens propios

---

### 3. Cerrar Sesión

**Endpoint**: `POST /api/auth/logout/`

**Descripción**: Cierra la sesión del usuario autenticado.

**Permisos**: Usuario autenticado (cualquier rol)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Body Parameters** (opcional):
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `refresh_token` | string | No | Refresh token a invalidar |

**Ejemplo de Request**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Ejemplo de Response Exitosa** (200 OK):
```json
{
  "success": true,
  "message": "Sesión cerrada exitosamente"
}
```

**Errores**:

```json
// 401 Unauthorized - No autenticado
{
  "detail": "Authentication credentials were not provided."
}

// 400 Bad Request - Error al cerrar sesión
{
  "success": false,
  "error": "Error al cerrar la sesión. Por favor, intente nuevamente."
}
```

---

### 4. Verificar Sesión

**Endpoint**: `GET /api/auth/verificar-sesion/`

**Descripción**: Verifica si el usuario tiene una sesión activa válida.

**Permisos**: Usuario autenticado

**Headers**:
```
Authorization: Bearer <access_token>
```

**Ejemplo de Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "autenticado": true,
    "usuario": {
      "id": 5,
      "username": "juan_perez",
      "email": "juan@ejemplo.com",
      "first_name": "Juan",
      "last_name": "Pérez",
      "rol": "profesional",
      "foto_perfil": "/media/usuarios/juan.jpg"
    }
  }
}
```

**Uso**: 
- Frontend puede llamar este endpoint al cargar la aplicación
- Verifica si el token almacenado sigue siendo válido
- Obtiene información actualizada del usuario

---

### 5. Refrescar Token

**Endpoint**: `POST /api/auth/refresh/`

**Descripción**: Refresca el access token usando el refresh token.

**Permisos**: Acceso público

**Body Parameters**:
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `refresh` | string | Sí | Refresh token JWT |

**Ejemplo de Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Ejemplo de Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

**Errores**:

```json
// 400 Bad Request - Token inválido o en blacklist
{
  "success": false,
  "error": "Token inválido o expirado"
}
```

---

## Seguridad

### 1. Autenticación JWT

**Configuración**:
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),   # 60 minutos
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # 7 días
    'ROTATE_REFRESH_TOKENS': True,                    # Rota en cada refresh
    'BLACKLIST_AFTER_ROTATION': True,                 # Invalida token anterior
    'UPDATE_LAST_LOGIN': True,                        # Actualiza last_login
}
```

**Claims en el Token**:
```json
{
  "token_type": "access",
  "exp": 1641060000,
  "iat": 1641056400,
  "jti": "a1b2c3d4e5f6",
  "user_id": 5,
  "username": "juan_perez",
  "email": "juan@ejemplo.com",
  "rol": "profesional"
}
```

### 2. Rate Limiting (Anti Fuerza Bruta)

**Configuración**:
- **Máximo de intentos**: 5 intentos fallidos
- **Período de bloqueo**: 15 minutos
- **Alcance**: Por email (no por IP)

**Funcionamiento**:
```python
# AuthService en auth_services.py
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

_failed_attempts = {}  # {email: count}
_lockout_times = {}    # {email: datetime}
```

**Notas de Producción**:
- Usar Redis/Memcached en lugar de diccionarios en memoria
- Considerar agregar rate limiting por IP también

### 3. Blacklist de Tokens

**Funcionamiento**:
- Refresh tokens invalidados se agregan a blacklist
- Tokens en blacklist no pueden usarse para refrescar
- Access tokens siguen válidos hasta expirar (máx 60 min)

**Implementación**:
```python
# En memoria (desarrollo)
_token_blacklist = set()

# Producción: usar djangorestframework-simplejwt.token_blacklist
# O Redis con expiración automática
```

### 4. Validación de Google OAuth

**Seguridad**:
- ✅ Validación directa con Google API (no confianza ciega en el frontend)
- ✅ Verificación de email confirmado
- ✅ Validación de firma del token
- ✅ Verificación de audiencia (client_id)
- ✅ Verificación de emisor (Google)

```python
idinfo = id_token.verify_oauth2_token(
    google_token,
    requests.Request(),
    settings.GOOGLE_OAUTH_CLIENT_ID
)
```

### 5. Protección de Datos

**Nunca se revelan**:
- Si un email existe o no en el sistema
- Si el error es en email o contraseña
- Detalles internos del sistema

**Respuestas genéricas**:
```json
{
  "error": "Credenciales inválidas"  // No dice cuál dato es incorrecto
}
```

### 6. Logging y Auditoría

**Se registran**:
- ✅ Todos los intentos de login (exitosos y fallidos)
- ✅ Bloqueos por intentos fallidos
- ✅ Cierres de sesión
- ✅ Errores de autenticación
- ✅ Validaciones de Google

**Nivel de logs**:
- `INFO`: Logins exitosos, logouts
- `WARNING`: Intentos fallidos, bloqueos, tokens inválidos
- `ERROR`: Errores inesperados del sistema

---

## Flujos de Autenticación

### Flujo 1: Login con Email/Password

```
┌─────────┐                ┌──────────┐                ┌──────────┐
│ Cliente │                │ Backend  │                │    BD    │
└────┬────┘                └────┬─────┘                └────┬─────┘
     │                          │                           │
     │  POST /api/auth/login/   │                           │
     │  {email, password}       │                           │
     │─────────────────────────>│                           │
     │                          │  Buscar usuario           │
     │                          │──────────────────────────>│
     │                          │                           │
     │                          │  Usuario encontrado       │
     │                          │<──────────────────────────│
     │                          │                           │
     │                          │  Verificar password hash  │
     │                          │───────┐                   │
     │                          │       │                   │
     │                          │<──────┘                   │
     │                          │                           │
     │                          │  Generar JWT tokens       │
     │                          │───────┐                   │
     │                          │       │                   │
     │                          │<──────┘                   │
     │                          │                           │
     │                          │  Actualizar last_login    │
     │                          │──────────────────────────>│
     │                          │                           │
     │  200 OK                  │                           │
     │  {usuario, tokens}       │                           │
     │<─────────────────────────│                           │
     │                          │                           │
     │  Guardar tokens          │                           │
     │  en localStorage         │                           │
     │────────┐                 │                           │
     │        │                 │                           │
     │<───────┘                 │                           │
     │                          │                           │
```

### Flujo 2: Login con Google OAuth

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Cliente │    │ Google   │    │ Backend  │    │    BD    │
└────┬────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │              │               │               │
     │  Click Google│               │               │
     │  Sign-In     │               │               │
     │──────────────>               │               │
     │              │               │               │
     │  Google Login│               │               │
     │  Dialog      │               │               │
     │<─────────────│               │               │
     │              │               │               │
     │  Autorizar   │               │               │
     │──────────────>               │               │
     │              │               │               │
     │  Google Token│               │               │
     │<─────────────│               │               │
     │              │               │               │
     │  POST /api/auth/login/google/ │               │
     │  {token}     │               │               │
     │──────────────────────────────>               │
     │              │               │  Validar token│
     │              │               │  con Google   │
     │              │               │───────────────>
     │              │               │               │
     │              │               │  Token válido │
     │              │               │<──────────────│
     │              │               │               │
     │              │               │  Buscar usuario│
     │              │               │──────────────>│
     │              │               │               │
     │              │               │  Usuario      │
     │              │               │<──────────────│
     │              │               │               │
     │              │               │  Generar JWT  │
     │              │               │───────┐       │
     │              │               │       │       │
     │              │               │<──────┘       │
     │              │               │               │
     │  200 OK      │               │               │
     │  {usuario, tokens}            │               │
     │<──────────────────────────────│               │
     │              │               │               │
```

### Flujo 3: Refresh Token

```
┌─────────┐                ┌──────────┐
│ Cliente │                │ Backend  │
└────┬────┘                └────┬─────┘
     │                          │
     │  Request API             │
     │  (access token expirado) │
     │─────────────────────────>│
     │                          │
     │  401 Unauthorized        │
     │<─────────────────────────│
     │                          │
     │  POST /api/auth/refresh/ │
     │  {refresh}               │
     │─────────────────────────>│
     │                          │
     │                          │  Validar refresh
     │                          │  No en blacklist
     │                          │───────┐
     │                          │       │
     │                          │<──────┘
     │                          │
     │                          │  Generar nuevo
     │                          │  access token
     │                          │───────┐
     │                          │       │
     │                          │<──────┘
     │                          │
     │  200 OK                  │
     │  {access}                │
     │<─────────────────────────│
     │                          │
     │  Reintentar request      │
     │  original con nuevo token│
     │─────────────────────────>│
     │                          │
     │  200 OK                  │
     │  {data}                  │
     │<─────────────────────────│
     │                          │
```

### Flujo 4: Logout

```
┌─────────┐                ┌──────────┐
│ Cliente │                │ Backend  │
└────┬────┘                └────┬─────┘
     │                          │
     │  POST /api/auth/logout/  │
     │  Header: Bearer token    │
     │  {refresh_token}         │
     │─────────────────────────>│
     │                          │
     │                          │  Agregar refresh
     │                          │  a blacklist
     │                          │───────┐
     │                          │       │
     │                          │<──────┘
     │                          │
     │                          │  Destruir sesión
     │                          │  Django
     │                          │───────┐
     │                          │       │
     │                          │<──────┘
     │                          │
     │  200 OK                  │
     │  {success}               │
     │<─────────────────────────│
     │                          │
     │  Limpiar localStorage    │
     │────────┐                 │
     │        │                 │
     │<───────┘                 │
     │                          │
     │  Redirigir a login       │
     │────────┐                 │
     │        │                 │
     │<───────┘                 │
     │                          │
```

---

## Tokens JWT

### Estructura del Token

**Access Token**:
```json
{
  "token_type": "access",
  "exp": 1641060000,        // Expira en 60 minutos
  "iat": 1641056400,        // Emitido ahora
  "jti": "a1b2c3d4e5f6",   // ID único del token
  "user_id": 5,
  "username": "juan_perez",
  "email": "juan@ejemplo.com",
  "rol": "profesional"
}
```

**Refresh Token**:
```json
{
  "token_type": "refresh",
  "exp": 1641660000,        // Expira en 7 días
  "iat": 1641056400,
  "jti": "f6e5d4c3b2a1",
  "user_id": 5,
  "username": "juan_perez",
  "email": "juan@ejemplo.com",
  "rol": "profesional"
}
```

### Uso de Tokens

**1. Guardar tokens (Frontend)**:
```javascript
// Tras login exitoso
localStorage.setItem('access_token', response.data.tokens.access);
localStorage.setItem('refresh_token', response.data.tokens.refresh);
```

**2. Usar access token en requests**:
```javascript
fetch('/api/alguna-ruta/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  }
});
```

**3. Refrescar cuando expira**:
```javascript
// Interceptor de Axios (ejemplo)
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response.status === 401) {
      // Token expirado, refrescar
      const refreshToken = localStorage.getItem('refresh_token');
      const response = await fetch('/api/auth/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken })
      });
      
      const data = await response.json();
      localStorage.setItem('access_token', data.data.access);
      
      // Reintentar request original
      error.config.headers['Authorization'] = `Bearer ${data.data.access}`;
      return axios.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

**4. Limpiar al logout**:
```javascript
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

---

## Ejemplos de Uso

### Ejemplo 1: Login Completo (Frontend React)

```javascript
import React, { useState } from 'react';
import axios from 'axios';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await axios.post('/api/auth/login/', {
        email,
        password
      });
      
      // Guardar tokens
      localStorage.setItem('access_token', response.data.data.tokens.access);
      localStorage.setItem('refresh_token', response.data.data.tokens.refresh);
      
      // Guardar info del usuario
      localStorage.setItem('user', JSON.stringify(response.data.data.usuario));
      
      // Redirigir según el rol
      const rol = response.data.data.usuario.rol;
      if (rol === 'administrador') {
        window.location.href = '/admin/dashboard';
      } else if (rol === 'profesional') {
        window.location.href = '/profesional/dashboard';
      } else {
        window.location.href = '/cliente/dashboard';
      }
      
    } catch (err) {
      if (err.response) {
        setError(err.response.data.error);
      } else {
        setError('Error de conexión. Por favor, intente nuevamente.');
      }
    }
  };
  
  return (
    <form onSubmit={handleLogin}>
      {error && <div className="error">{error}</div>}
      
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      
      <input
        type="password"
        placeholder="Contraseña"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      
      <button type="submit">Iniciar Sesión</button>
    </form>
  );
};

export default LoginForm;
```

### Ejemplo 2: Google Login (Frontend React)

```javascript
import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const GoogleLoginButton = () => {
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const response = await axios.post('/api/auth/login/google/', {
        token: credentialResponse.credential
      });
      
      // Guardar tokens
      localStorage.setItem('access_token', response.data.data.tokens.access);
      localStorage.setItem('refresh_token', response.data.data.tokens.refresh);
      localStorage.setItem('user', JSON.stringify(response.data.data.usuario));
      
      // Redirigir
      window.location.href = '/dashboard';
      
    } catch (err) {
      console.error('Error en login con Google:', err);
      alert(err.response?.data?.error || 'Error al iniciar sesión con Google');
    }
  };
  
  const handleGoogleError = () => {
    console.error('Error en Google OAuth');
    alert('Error al iniciar sesión con Google');
  };
  
  return (
    <GoogleLogin
      onSuccess={handleGoogleSuccess}
      onError={handleGoogleError}
      useOneTap
    />
  );
};

export default GoogleLoginButton;
```

### Ejemplo 3: Logout (Frontend)

```javascript
import axios from 'axios';

const logout = async () => {
  try {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    await axios.post('/api/auth/logout/', 
      { refresh_token: refreshToken },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    // Limpiar localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // Redirigir a login
    window.location.href = '/login';
    
  } catch (err) {
    console.error('Error en logout:', err);
    // Limpiar de todas formas
    localStorage.clear();
    window.location.href = '/login';
  }
};

export default logout;
```

### Ejemplo 4: Axios Interceptor para Auto-Refresh

```javascript
import axios from 'axios';

// Configurar interceptor
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    // Si el token expiró y no hemos intentado refrescar aún
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/auth/refresh/', {
          refresh: refreshToken
        });
        
        const newAccessToken = response.data.data.access;
        localStorage.setItem('access_token', newAccessToken);
        
        // Reintentar request original
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        return axios(originalRequest);
        
      } catch (refreshError) {
        // Refresh token también expiró
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default axios;
```

---

## Testing

### Tests Implementados

Se han implementado **25+ tests unitarios** que cubren todos los casos de uso:

#### Tests para CU-07 (Iniciar Sesión)

**Login con Email/Password**:
```python
class LoginEmailPasswordTestCase(TestCase):
    def test_login_exitoso(self):
        """Login exitoso con credenciales correctas"""
        
    def test_login_email_incorrecto(self):
        """Login con email inexistente"""
        
    def test_login_password_incorrecta(self):
        """Login con contraseña incorrecta"""
        
    def test_login_usuario_inactivo(self):
        """No puede hacer login un usuario inactivo"""
        
    def test_rate_limiting_intentos_fallidos(self):
        """Bloqueo tras múltiples intentos fallidos"""
        
    def test_reset_intentos_tras_login_exitoso(self):
        """Los intentos fallidos se resetean tras login exitoso"""
        
    def test_actualiza_last_login(self):
        """Se actualiza la fecha de último login"""
```

**Login con Google**:
```python
class LoginGoogleTestCase(TestCase):
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_exitoso(self, mock_verify):
        """Login exitoso con Google OAuth"""
        
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_vincula_cuenta_existente(self, mock_verify):
        """Vincula cuenta existente sin Google ID"""
        
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_email_no_verificado(self, mock_verify):
        """No permite login con email no verificado"""
        
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_usuario_no_registrado(self, mock_verify):
        """No permite login de usuario no registrado"""
        
    @patch('apps.usuarios.auth_services.id_token.verify_oauth2_token')
    def test_login_google_token_invalido(self, mock_verify):
        """Manejo de token de Google inválido"""
```

#### Tests para CU-08 (Cerrar Sesión)

```python
class LogoutTestCase(TestCase):
    def test_logout_exitoso(self):
        """Logout exitoso"""
        
    def test_logout_invalida_refresh_token(self):
        """Logout invalida el refresh token"""
        
    def test_logout_sin_refresh_token(self):
        """Logout sin proporcionar refresh token"""
        
    def test_logout_con_request_django(self):
        """Logout con sesión Django"""
```

#### Tests para Gestión de Tokens

```python
class TokenManagementTestCase(TestCase):
    def test_genera_tokens_jwt(self):
        """Genera tokens JWT correctamente"""
        
    def test_identifica_rol_cliente(self):
        """Identifica correctamente rol de cliente"""
        
    def test_identifica_rol_profesional(self):
        """Identifica correctamente rol de profesional"""
        
    def test_identifica_rol_administrador(self):
        """Identifica correctamente rol de administrador"""
        
    def test_blacklist_token(self):
        """Agregar token a blacklist"""
        
    def test_get_remaining_lockout_time(self):
        """Obtener tiempo restante de bloqueo"""
```

### Ejecutar Tests

```bash
# Todos los tests de autenticación
python manage.py test apps.usuarios.tests_auth_services

# Con verbose
python manage.py test apps.usuarios.tests_auth_services --verbosity=2

# Con coverage
coverage run --source='apps.usuarios' manage.py test apps.usuarios.tests_auth_services
coverage report
```

---

## Rate Limiting

### Configuración Actual

```python
# En auth_services.py
MAX_LOGIN_ATTEMPTS = 5              # Máximo de intentos fallidos
LOCKOUT_DURATION_MINUTES = 15       # Duración del bloqueo en minutos

_failed_attempts = {}               # {email: count}
_lockout_times = {}                 # {email: datetime}
```

### Comportamiento

1. **Registro de Intentos**:
   - Cada login fallido incrementa el contador
   - Los intentos se asocian al email (no a la IP)

2. **Bloqueo**:
   - Al alcanzar 5 intentos, se bloquea por 15 minutos
   - Durante el bloqueo, ni siquiera con la contraseña correcta se puede entrar

3. **Reset**:
   - Los intentos se resetean tras un login exitoso
   - El bloqueo expira automáticamente tras 15 minutos

### Mejoras para Producción

**Opción 1: Django-ratelimit**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='post:email', rate='5/15m', method='POST')
@api_view(['POST'])
def login_email_password_api(request):
    # ...
```

**Opción 2: Redis**
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_rate_limit(email):
    key = f"login_attempts:{email}"
    attempts = redis_client.get(key)
    
    if attempts and int(attempts) >= 5:
        ttl = redis_client.ttl(key)
        raise ValueError(f"Bloqueado. {ttl//60} minutos restantes.")
    
    redis_client.incr(key)
    redis_client.expire(key, 900)  # 15 minutos
```

**Opción 3: django-axes**
```python
# Paquete completo para tracking de intentos fallidos
pip install django-axes

# settings.py
INSTALLED_APPS += ['axes']
MIDDLEWARE += ['axes.middleware.AxesMiddleware']

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ['email']
```

---

## Troubleshooting

### Problema 1: Token expirado constantemente

**Síntoma**: Access token expira muy rápido

**Solución**:
```python
# En settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Aumentar si es necesario
}
```

### Problema 2: Error "Token inválido" tras logout

**Síntoma**: Refresh token dice inválido inmediatamente después de logout

**Causa**: Token está en blacklist

**Solución**: Es el comportamiento esperado. El frontend debe manejar este caso y redirigir a login.

### Problema 3: Google OAuth no funciona

**Síntoma**: Error al validar token de Google

**Verificar**:
1. `GOOGLE_OAUTH_CLIENT_ID` en settings.py
2. Token se obtiene correctamente en frontend
3. Dependencia `google-auth` instalada
```bash
pip install google-auth
```

### Problema 4: Usuarios bloqueados indefinidamente

**Síntoma**: Usuario bloqueado y no puede entrar nunca

**Causa**: Blacklist en memoria se pierde al reiniciar servidor

**Solución Temporal**:
```python
# Limpiar manualmente
AuthService._failed_attempts = {}
AuthService._lockout_times = {}
```

**Solución Permanente**: Usar Redis para persistencia

### Problema 5: CORS errors en frontend

**Síntoma**: Errores de CORS al llamar API desde frontend

**Solución**:
```bash
pip install django-cors-headers
```

```python
# settings.py
INSTALLED_APPS += ['corsheaders']

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... otros middleware
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",    # React dev server
    "http://localhost:8080",    # Vue dev server
]

# O para desarrollo:
CORS_ALLOW_ALL_ORIGINS = True  # ⚠️ Solo desarrollo
```

---

## Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias nuevas**:
- `djangorestframework-simplejwt==5.3.1`
- `google-auth==2.35.0`

### 2. Configurar Google OAuth

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar Google+ API
3. Crear credenciales OAuth 2.0
4. Agregar a `settings.py`:

```python
GOOGLE_OAUTH_CLIENT_ID = 'tu-client-id.apps.googleusercontent.com'
```

### 3. Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará las tablas necesarias para token blacklist.

### 4. Prueba

```bash
# Iniciar servidor
python manage.py runserver

# Probar endpoint
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'
```

---

## Resumen de Archivos Creados/Modificados

### Nuevos Archivos (3)
1. **apps/usuarios/auth_services.py** (~700 líneas)
   - `AuthService` con métodos para login y logout
   
2. **apps/usuarios/auth_api_views.py** (~550 líneas)
   - 5 endpoints REST de autenticación
   
3. **apps/usuarios/auth_urls.py** (~50 líneas)
   - Rutas de autenticación
   
4. **apps/usuarios/tests_auth_services.py** (~550 líneas)
   - 25+ tests unitarios
   
5. **API_AUTENTICACION_DOCUMENTATION.md** (este archivo, ~2000 líneas)
   - Documentación completa

### Archivos Modificados (4)
1. **apps/usuarios/serializers.py** (+~100 líneas)
   - 5 nuevos serializers de autenticación
   
2. **servihogar/settings.py** (+~60 líneas)
   - Configuración JWT y apps necesarias
   
3. **servihogar/urls.py** (+1 línea)
   - Ruta `/api/auth/`
   
4. **requirements.txt** (+2 líneas)
   - Dependencias JWT y Google Auth

---

## Próximos Pasos

1. ✅ CU-07 y CU-08 implementados (COMPLETADO)
2. ⏳ Integrar con frontend
3. ⏳ Implementar rate limiting con Redis (producción)
4. ⏳ Agregar autenticación de dos factores (2FA)
5. ⏳ Implementar "Recordarme" (remember me)
6. ⏳ Agregar recuperación de contraseña

---

**Fecha de creación**: 2025-11-05  
**Versión**: 1.0.0  
**Autor**: Equipo ServiHogar
