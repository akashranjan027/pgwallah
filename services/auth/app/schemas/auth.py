"""
Pydantic schemas for authentication endpoints
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import UserRole, IDProofType


# Request schemas
class RegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number in +91 format")
    role: UserRole = Field(default=UserRole.TENANT, description="User role")

    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character'
            )
        return v

    @validator('phone')
    def validate_phone(cls, v):
        """Validate Indian phone number format"""
        if v is None:
            return v
        
        import re
        pattern = r'^\+91[6-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in +91XXXXXXXXXX format')
        return v


class LoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class RefreshRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str = Field(..., description="Refresh token")


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password complexity"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character'
            )
        return v


class UpdateProfileRequest(BaseModel):
    """Update profile request schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None)
    occupation: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    id_proof_type: Optional[IDProofType] = Field(None)
    id_proof_number: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

    @validator('phone', 'emergency_contact_phone')
    def validate_phone_numbers(cls, v):
        """Validate phone number format"""
        if v is None:
            return v
        
        import re
        pattern = r'^\+91[6-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in +91XXXXXXXXXX format')
        return v

    @validator('pincode')
    def validate_pincode(cls, v):
        """Validate Indian pincode format"""
        if v is None:
            return v
        
        import re
        pattern = r'^\d{6}$'
        if not re.match(pattern, v):
            raise ValueError('Pincode must be 6 digits')
        return v


# Response schemas
class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    email: str
    full_name: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantProfileResponse(BaseModel):
    """Tenant profile response schema"""
    id: UUID
    user_id: UUID
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    occupation: Optional[str]
    company: Optional[str]
    id_proof_type: Optional[IDProofType]
    id_proof_number: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="User information")


class ProfileResponse(BaseModel):
    """Profile response schema"""
    user: UserResponse
    tenant_profile: Optional[TenantProfileResponse] = None

    class Config:
        from_attributes = True


class JWKSResponse(BaseModel):
    """JWKS response schema"""
    keys: list[dict] = Field(..., description="JSON Web Keys")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageResponse(BaseModel):
    """Simple message response schema"""
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)