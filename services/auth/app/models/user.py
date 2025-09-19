"""
User and related database models
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    """User role enumeration"""
    TENANT = "tenant"
    ADMIN = "admin"
    STAFF = "staff"


class IDProofType(str, Enum):
    """ID proof type enumeration"""
    AADHAAR = "aadhaar"
    PAN = "pan"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"


class User(Base):
    """User model"""
    
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(15),
        index=True,
        nullable=True
    )
    
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.TENANT,
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    reset_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    login_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    tenant_profile: Mapped[Optional["TenantProfile"]] = relationship(
        "TenantProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

    @property
    def is_tenant(self) -> bool:
        """Check if user is a tenant"""
        return self.role == UserRole.TENANT

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN

    @property
    def is_staff(self) -> bool:
        """Check if user is staff"""
        return self.role == UserRole.STAFF

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until


class TenantProfile(Base):
    """Tenant profile model - extended information for tenant users"""
    
    __tablename__ = "tenant_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )
    
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True
    )
    
    occupation: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    company: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    id_proof_type: Mapped[Optional[IDProofType]] = mapped_column(
        SQLEnum(IDProofType),
        nullable=True
    )
    
    id_proof_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tenant_profile"
    )

    def __repr__(self) -> str:
        return f"<TenantProfile user_id={self.user_id}>"


class RefreshToken(Base):
    """Refresh token model for tracking issued refresh tokens"""
    
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    jti: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<RefreshToken {self.jti} user_id={self.user_id}>"

    @property
    def is_expired(self) -> bool:
        """Check if refresh token is expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if refresh token is valid (not revoked and not expired)"""
        return not self.is_revoked and not self.is_expired