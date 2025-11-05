"""
Servicios de autenticación para los casos de uso CU-07 y CU-08.
Gestiona inicio y cierre de sesión con múltiples métodos de autenticación.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

Usuario = get_user_model()
logger = logging.getLogger(__name__)


class AuthService:
    """
    Servicio para gestión de autenticación.
    Implementa CU-07 (Iniciar Sesión) y CU-08 (Cerrar Sesión).
    """
    
    # Configuración de rate limiting (intentos fallidos)
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    # Cache para tracking de intentos fallidos (en producción usar Redis/Memcached)
    _failed_attempts = {}
    _lockout_times = {}
    
    # Blacklist de tokens (en producción usar Redis)
    _token_blacklist = set()
    
    # ========================================================================
    # CU-07: INICIAR SESIÓN
    # ========================================================================
    
    @classmethod
    def login_email_password(
        cls,
        email: str,
        password: str,
        request=None
    ) -> Dict:
        """
        Inicia sesión con email y contraseña.
        
        Proceso:
        1. Verificar rate limiting (protección contra fuerza bruta)
        2. Buscar usuario por email
        3. Verificar que el usuario esté activo
        4. Validar contraseña
        5. Generar tokens JWT
        6. Registrar acceso exitoso
        7. Actualizar último login
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            request: Objeto request de Django (opcional, para sesión)
            
        Returns:
            Dict con información del usuario y tokens
            
        Raises:
            ValueError: Si las credenciales son inválidas o el usuario está bloqueado
        """
        
        # 1. Verificar rate limiting
        if cls._is_locked_out(email):
            lockout_time = cls._lockout_times.get(email)
            remaining_minutes = cls._get_remaining_lockout_time(email)
            
            logger.warning(
                f"Intento de login bloqueado para {email}. "
                f"Quedan {remaining_minutes} minutos de bloqueo."
            )
            
            raise ValueError(
                f"Demasiados intentos fallidos. "
                f"Cuenta bloqueada temporalmente. "
                f"Intente nuevamente en {remaining_minutes} minutos."
            )
        
        try:
            # 2. Buscar usuario por email
            try:
                usuario = Usuario.objects.get(email=email)
            except Usuario.DoesNotExist:
                # No revelar si el email existe o no (seguridad)
                cls._register_failed_attempt(email)
                logger.warning(f"Intento de login con email inexistente: {email}")
                raise ValueError("Credenciales inválidas")
            
            # 3. Verificar que el usuario esté activo
            if not usuario.is_active:
                logger.warning(
                    f"Intento de login de usuario inactivo: {email} (ID: {usuario.id})"
                )
                raise ValueError(
                    "Esta cuenta está desactivada. "
                    "Contacte al administrador para más información."
                )
            
            # 4. Validar contraseña
            if not usuario.check_password(password):
                cls._register_failed_attempt(email)
                logger.warning(
                    f"Contraseña incorrecta para usuario: {email} (ID: {usuario.id})"
                )
                # No revelar qué dato es incorrecto (seguridad)
                raise ValueError("Credenciales inválidas")
            
            # 5. Login exitoso - resetear intentos fallidos
            cls._reset_failed_attempts(email)
            
            # 6. Generar tokens JWT
            tokens = cls._generate_tokens(usuario)
            
            # 7. Actualizar último login
            usuario.last_login = timezone.now()
            usuario.save(update_fields=['last_login'])
            
            # 8. Crear sesión en Django si se proporciona request
            if request:
                login(request, usuario)
            
            # 9. Determinar el rol del usuario
            rol = cls._get_user_role(usuario)
            
            # 10. Registrar login exitoso
            logger.info(
                f"Login exitoso: {usuario.username} ({email}) - Rol: {rol}"
            )
            
            return {
                'usuario': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'email': usuario.email,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'rol': rol,
                    'foto_perfil': usuario.foto_perfil.url if usuario.foto_perfil else None
                },
                'tokens': tokens,
                'mensaje': 'Inicio de sesión exitoso'
            }
            
        except ValueError:
            # Re-lanzar errores de validación
            raise
        except Exception as e:
            # Error inesperado
            logger.error(f"Error inesperado en login con email/password: {str(e)}")
            raise ValueError("Error al procesar el inicio de sesión")
    
    @classmethod
    def login_google(
        cls,
        google_token: str,
        request=None
    ) -> Dict:
        """
        Inicia sesión con Google OAuth.
        
        Proceso:
        1. Validar token de Google con la API oficial
        2. Extraer información del usuario (email, nombre, google_id)
        3. Buscar o crear usuario en la base de datos
        4. Verificar que el usuario esté activo
        5. Generar tokens JWT
        6. Registrar acceso
        
        Args:
            google_token: Token JWT de Google OAuth
            request: Objeto request de Django (opcional)
            
        Returns:
            Dict con información del usuario y tokens
            
        Raises:
            ValueError: Si el token es inválido o el usuario está bloqueado
        """
        
        try:
            # 1. Validar token con Google API
            idinfo = id_token.verify_oauth2_token(
                google_token,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
            
            # 2. Extraer información del token
            google_id = idinfo['sub']
            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified', False)
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')
            
            # Verificar que el email esté verificado
            if not email_verified:
                logger.warning(
                    f"Intento de login con Google usando email no verificado: {email}"
                )
                raise ValueError(
                    "El email de Google no está verificado. "
                    "Por favor, verifique su cuenta de Google."
                )
            
            if not email:
                logger.error("Token de Google sin email")
                raise ValueError("Token de Google inválido: email no encontrado")
            
            # 3. Buscar usuario por google_id o email
            usuario = None
            
            # Intentar buscar por google_id
            try:
                usuario = Usuario.objects.get(google_id=google_id)
            except Usuario.DoesNotExist:
                # Si no existe por google_id, buscar por email
                try:
                    usuario = Usuario.objects.get(email=email)
                    
                    # Si existe por email pero no tiene google_id, vincular cuenta
                    if not usuario.google_id:
                        usuario.google_id = google_id
                        usuario.save(update_fields=['google_id'])
                        logger.info(
                            f"Cuenta vinculada con Google: {email} (ID: {usuario.id})"
                        )
                        
                except Usuario.DoesNotExist:
                    # Usuario nuevo - debe registrarse primero
                    logger.info(
                        f"Intento de login con Google de usuario no registrado: {email}"
                    )
                    raise ValueError(
                        "Usuario no registrado. "
                        "Por favor, complete el registro primero."
                    )
            
            # 4. Verificar que el usuario esté activo
            if not usuario.is_active:
                logger.warning(
                    f"Intento de login Google de usuario inactivo: {email} (ID: {usuario.id})"
                )
                raise ValueError(
                    "Esta cuenta está desactivada. "
                    "Contacte al administrador para más información."
                )
            
            # 5. Generar tokens JWT
            tokens = cls._generate_tokens(usuario)
            
            # 6. Actualizar último login
            usuario.last_login = timezone.now()
            usuario.save(update_fields=['last_login'])
            
            # 7. Crear sesión en Django si se proporciona request
            if request:
                # Para Google OAuth, necesitamos hacer login sin contraseña
                usuario.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, usuario)
            
            # 8. Determinar el rol
            rol = cls._get_user_role(usuario)
            
            # 9. Registrar login exitoso
            logger.info(
                f"Login Google exitoso: {usuario.username} ({email}) - Rol: {rol}"
            )
            
            return {
                'usuario': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'email': usuario.email,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'rol': rol,
                    'foto_perfil': usuario.foto_perfil.url if usuario.foto_perfil else None
                },
                'tokens': tokens,
                'mensaje': 'Inicio de sesión exitoso con Google'
            }
            
        except ValueError:
            # Re-lanzar errores de validación
            raise
        except Exception as e:
            # Error de validación de token de Google
            logger.error(f"Error al validar token de Google: {str(e)}")
            raise ValueError(
                "Token de Google inválido o expirado. "
                "Por favor, intente iniciar sesión nuevamente."
            )
    
    # ========================================================================
    # CU-08: CERRAR SESIÓN
    # ========================================================================
    
    @classmethod
    def logout_user(
        cls,
        usuario,
        refresh_token: Optional[str] = None,
        request=None
    ) -> Dict:
        """
        Cierra la sesión del usuario.
        
        Proceso:
        1. Guardar datos relevantes de la sesión (ya gestionado por Django)
        2. Agregar refresh token a blacklist si se proporciona
        3. Destruir sesión de Django si existe
        4. Actualizar último logout (campo personalizado si existe)
        5. Registrar cierre de sesión
        
        Args:
            usuario: Instancia del usuario
            refresh_token: Token de refresh a invalidar (opcional)
            request: Objeto request de Django (opcional)
            
        Returns:
            Dict con confirmación del logout
            
        Raises:
            ValueError: Si hay error al cerrar sesión
        """
        
        try:
            # 1. Registrar intento de logout
            logger.info(f"Iniciando logout para usuario: {usuario.username} (ID: {usuario.id})")
            
            # 2. Invalidar refresh token si se proporciona
            if refresh_token:
                try:
                    # Agregar token a blacklist
                    cls._blacklist_token(refresh_token)
                    logger.info(f"Refresh token invalidado para usuario {usuario.id}")
                except Exception as e:
                    logger.warning(
                        f"Error al invalidar refresh token para usuario {usuario.id}: {str(e)}"
                    )
                    # No fallar el logout por esto
            
            # 3. Destruir sesión de Django
            if request and request.user.is_authenticated:
                # Django guarda automáticamente antes de logout
                logout(request)
                logger.info(f"Sesión Django destruida para usuario {usuario.id}")
            
            # 4. Registrar logout exitoso
            logger.info(f"Logout exitoso: {usuario.username} (ID: {usuario.id})")
            
            return {
                'success': True,
                'mensaje': 'Sesión cerrada exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error al cerrar sesión para usuario {usuario.id}: {str(e)}")
            raise ValueError("Error al cerrar la sesión. Por favor, intente nuevamente.")
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    @staticmethod
    def _generate_tokens(usuario) -> Dict[str, str]:
        """
        Genera tokens JWT (access y refresh) para el usuario.
        
        Args:
            usuario: Instancia del usuario
            
        Returns:
            Dict con access_token y refresh_token
        """
        refresh = RefreshToken.for_user(usuario)
        
        # Agregar claims personalizados al token
        refresh['username'] = usuario.username
        refresh['email'] = usuario.email
        refresh['rol'] = AuthService._get_user_role(usuario)
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    
    @staticmethod
    def _get_user_role(usuario) -> str:
        """
        Determina el rol del usuario.
        
        Args:
            usuario: Instancia del usuario
            
        Returns:
            String con el rol: 'administrador', 'profesional', 'cliente'
        """
        if usuario.is_staff and usuario.is_superuser:
            return 'administrador'
        elif hasattr(usuario, 'profesional'):
            return 'profesional'
        elif hasattr(usuario, 'cliente'):
            return 'cliente'
        else:
            return 'usuario'  # Fallback
    
    @classmethod
    def _is_locked_out(cls, email: str) -> bool:
        """
        Verifica si el email está bloqueado por intentos fallidos.
        
        Args:
            email: Email a verificar
            
        Returns:
            True si está bloqueado, False en caso contrario
        """
        if email not in cls._lockout_times:
            return False
        
        lockout_time = cls._lockout_times[email]
        lockout_duration = timedelta(minutes=cls.LOCKOUT_DURATION_MINUTES)
        
        if timezone.now() < lockout_time + lockout_duration:
            return True
        else:
            # El bloqueo ya expiró
            del cls._lockout_times[email]
            del cls._failed_attempts[email]
            return False
    
    @classmethod
    def _get_remaining_lockout_time(cls, email: str) -> int:
        """
        Obtiene los minutos restantes de bloqueo.
        
        Args:
            email: Email a verificar
            
        Returns:
            Minutos restantes de bloqueo
        """
        if email not in cls._lockout_times:
            return 0
        
        lockout_time = cls._lockout_times[email]
        lockout_duration = timedelta(minutes=cls.LOCKOUT_DURATION_MINUTES)
        end_time = lockout_time + lockout_duration
        remaining = end_time - timezone.now()
        
        return max(0, int(remaining.total_seconds() / 60))
    
    @classmethod
    def _register_failed_attempt(cls, email: str):
        """
        Registra un intento fallido de login.
        
        Args:
            email: Email del intento fallido
        """
        if email not in cls._failed_attempts:
            cls._failed_attempts[email] = 0
        
        cls._failed_attempts[email] += 1
        
        # Si alcanza el máximo, bloquear
        if cls._failed_attempts[email] >= cls.MAX_LOGIN_ATTEMPTS:
            cls._lockout_times[email] = timezone.now()
            logger.warning(
                f"Email bloqueado por {cls.LOCKOUT_DURATION_MINUTES} minutos "
                f"tras {cls.MAX_LOGIN_ATTEMPTS} intentos fallidos: {email}"
            )
    
    @classmethod
    def _reset_failed_attempts(cls, email: str):
        """
        Resetea los intentos fallidos tras login exitoso.
        
        Args:
            email: Email a resetear
        """
        if email in cls._failed_attempts:
            del cls._failed_attempts[email]
        if email in cls._lockout_times:
            del cls._lockout_times[email]
    
    @classmethod
    def _blacklist_token(cls, token: str):
        """
        Agrega un token a la blacklist.
        
        Args:
            token: Token a invalidar
            
        Note:
            En producción, usar Redis o base de datos para persistencia.
        """
        cls._token_blacklist.add(token)
    
    @classmethod
    def is_token_blacklisted(cls, token: str) -> bool:
        """
        Verifica si un token está en la blacklist.
        
        Args:
            token: Token a verificar
            
        Returns:
            True si está en blacklist, False en caso contrario
        """
        return token in cls._token_blacklist
    
    @classmethod
    def verify_token(cls, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un token es válido y no está en blacklist.
        
        Args:
            token: Token a verificar
            
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        # Verificar blacklist
        if cls.is_token_blacklisted(token):
            return False, "Token inválido o expirado"
        
        try:
            # Verificar token JWT
            RefreshToken(token)
            return True, None
        except Exception as e:
            return False, "Token inválido o expirado"
