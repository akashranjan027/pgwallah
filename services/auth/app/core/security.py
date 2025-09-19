"""
Security utilities for JWT tokens and password hashing
"""
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


class SecurityManager:
    """Manages security operations including JWT and password hashing"""

    def __init__(self):
        # Password hashing context
        self.pwd_context = CryptContext(
            schemes=settings.PWD_CONTEXT_SCHEMES,
            deprecated=settings.PWD_CONTEXT_DEPRECATED,
        )
        
        # Generate RSA key pair for JWT signing (in production, load from files)
        self._private_key, self._public_key = self._generate_rsa_keys()
        
    def _generate_rsa_keys(self) -> tuple[bytes, bytes]:
        """Generate RSA key pair for JWT signing"""
        if settings.is_production:
            # In production, these should be loaded from secure storage
            # For now, we'll generate them (they should be persistent)
            pass
            
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem

    @property
    def private_key(self) -> bytes:
        """Get private key for signing"""
        return self._private_key

    @property
    def public_key(self) -> bytes:
        """Get public key for verification"""
        return self._public_key

    def get_public_key_jwk(self) -> Dict[str, Any]:
        """Get public key in JWK format for JWKS endpoint"""
        from cryptography.hazmat.primitives import serialization
        
        public_key_obj = serialization.load_pem_public_key(self._public_key)
        public_numbers = public_key_obj.public_numbers()
        
        return {
            "kty": "RSA",
            "use": "sig",
            "kid": "auth-key-1",
            "alg": settings.JWT_ALGORITHM,
            "n": self._int_to_base64url(public_numbers.n),
            "e": self._int_to_base64url(public_numbers.e),
        }

    def _int_to_base64url(self, value: int) -> str:
        """Convert integer to base64url encoded string"""
        import base64
        
        # Convert to bytes
        byte_length = (value.bit_length() + 7) // 8
        value_bytes = value.to_bytes(byte_length, byteorder='big')
        
        # Base64 encode and make URL safe
        return base64.urlsafe_b64encode(value_bytes).decode('utf-8').rstrip('=')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)

    def create_access_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        # Base claims
        to_encode = {
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "sub": str(subject),
            "type": "access",
        }

        # Add extra claims if provided
        if extra_claims:
            to_encode.update(extra_claims)

        return jwt.encode(
            to_encode,
            self._private_key,
            algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(
        self,
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT refresh token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )

        to_encode = {
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "sub": str(subject),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),  # Unique token ID
        }

        return jwt.encode(
            to_encode,
            self._private_key,
            algorithm=settings.JWT_ALGORITHM
        )

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[settings.JWT_ALGORITHM],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
            )
            return payload
        except JWTError:
            return None

    def extract_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None

    def is_token_type_valid(self, token: str, expected_type: str) -> bool:
        """Check if token is of expected type (access/refresh)"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("type") == expected_type
        return False

    def generate_reset_token(self) -> str:
        """Generate a secure reset token"""
        return secrets.token_urlsafe(32)

    def generate_verification_token(self) -> str:
        """Generate a secure email verification token"""
        return secrets.token_urlsafe(32)


# Global security manager instance
security_manager = SecurityManager()


# Convenience functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return security_manager.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return security_manager.get_password_hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create JWT access token"""
    return security_manager.create_access_token(subject, expires_delta, extra_claims)


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT refresh token"""
    return security_manager.create_refresh_token(subject, expires_delta)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    return security_manager.verify_token(token)