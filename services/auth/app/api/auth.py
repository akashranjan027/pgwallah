"""
Authentication API endpoints
"""
from datetime import datetime, timedelta
from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    security_manager,
    verify_password,
    verify_token,
)
from app.models.user import RefreshToken, TenantProfile, User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    JWKSResponse,
    LoginRequest,
    MessageResponse,
    ProfileResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

# Utility to fully materialize user for pydantic serialization and avoid async IO
USER_RESPONSE_ATTRS = [
    "id", "email", "full_name", "phone", "role",
    "is_active", "is_verified", "last_login",
    "created_at", "updated_at",
]

async def load_user_for_response(db: AsyncSession, user: User) -> UserResponse:
    """Ensure all scalar attributes used by UserResponse are loaded to avoid async IO during serialization."""
    try:
        await db.refresh(user, attribute_names=USER_RESPONSE_ATTRS)
    except Exception as e:
        logger.warning(
            "User refresh for response failed",
            user_id=str(getattr(user, "id", None)),
            error=str(e),
        )
    return UserResponse.model_validate(user)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    stmt = select(User).options(selectinload(User.tenant_profile)).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is locked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    logger.info("User registration attempt", email=request.email, role=request.role)
    
    # Check if user already exists
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        logger.warning("Registration failed - user exists", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(request.password)
    
    user = User(
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        phone=request.phone,
        role=request.role,
        is_active=True,
        is_verified=False,  # Email verification required
    )
    
    db.add(user)
    await db.flush()  # Get user ID
    
    # Create tenant profile if user is a tenant
    if request.role == UserRole.TENANT:
        tenant_profile = TenantProfile(user_id=user.id)
        db.add(tenant_profile)
    
    await db.commit()
    await db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "email": user.email}
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Store refresh token
    refresh_token_payload = verify_token(refresh_token)
    if refresh_token_payload:
        refresh_token_record = RefreshToken(
            jti=refresh_token_payload["jti"],
            user_id=user.id,
            expires_at=datetime.utcfromtimestamp(refresh_token_payload["exp"])
        )
        db.add(refresh_token_record)
        await db.commit()
    
    logger.info("User registered successfully", user_id=str(user.id), email=user.email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=await load_user_for_response(db, user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens"""
    logger.info("User login attempt", email=request.email)
    
    # Fetch user
    stmt = select(User).options(selectinload(User.tenant_profile)).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        # Increment login attempts if user exists
        if user:
            user.login_attempts += 1
            if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.LOGIN_ATTEMPT_TIMEOUT_MINUTES
                )
                logger.warning(
                    "User account locked due to failed attempts",
                    user_id=str(user.id),
                    attempts=user.login_attempts
                )
            await db.commit()
        
        logger.warning("Login failed - invalid credentials", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        logger.warning("Login failed - inactive user", user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    if user.is_locked:
        logger.warning("Login failed - locked user", user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is locked due to too many failed attempts"
        )
    
    # Update user login info
    user.last_login = datetime.utcnow()
    user.login_attempts = 0  # Reset attempts on successful login
    user.locked_until = None
    
    # Generate tokens
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "email": user.email}
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Store refresh token
    refresh_token_payload = verify_token(refresh_token)
    if refresh_token_payload:
        refresh_token_record = RefreshToken(
            jti=refresh_token_payload["jti"],
            user_id=user.id,
            expires_at=datetime.utcfromtimestamp(refresh_token_payload["exp"])
        )
        db.add(refresh_token_record)
    
    await db.commit()
    # Important: refresh the user row so server-side onupdate columns (e.g., updated_at)
    # are loaded and no async IO is attempted during Pydantic model conversion.
    await db.refresh(user)
    
    logger.info("User logged in successfully", user_id=str(user.id), email=user.email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=await load_user_for_response(db, user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    logger.info("Token refresh attempt")
    
    # Verify refresh token
    payload = verify_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        logger.warning("Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token exists and is valid
    jti = payload.get("jti")
    user_id = payload.get("sub")
    
    stmt = select(RefreshToken).where(
        RefreshToken.jti == jti,
        RefreshToken.user_id == user_id
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()
    
    if not token_record or not token_record.is_valid:
        logger.warning("Refresh token not found or invalid", jti=jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Fetch user
    stmt = select(User).options(selectinload(User.tenant_profile)).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        logger.warning("User not found or inactive", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "email": user.email}
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    # Revoke old refresh token and store new one
    token_record.is_revoked = True
    
    new_payload = verify_token(new_refresh_token)
    if new_payload:
        new_token_record = RefreshToken(
            jti=new_payload["jti"],
            user_id=user.id,
            expires_at=datetime.utcfromtimestamp(new_payload["exp"])
        )
        db.add(new_token_record)
    
    await db.commit()
    
    logger.info("Token refreshed successfully", user_id=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=await load_user_for_response(db, user)
    )


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return ProfileResponse(
        user=UserResponse.model_validate(current_user),
        tenant_profile=current_user.tenant_profile
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    logger.info("Profile update attempt", user_id=str(current_user.id))
    
    # Update user fields
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.phone is not None:
        current_user.phone = request.phone
    
    # Update tenant profile if user is a tenant
    if current_user.is_tenant and current_user.tenant_profile:
        profile = current_user.tenant_profile
        
        if request.emergency_contact_name is not None:
            profile.emergency_contact_name = request.emergency_contact_name
        if request.emergency_contact_phone is not None:
            profile.emergency_contact_phone = request.emergency_contact_phone
        if request.occupation is not None:
            profile.occupation = request.occupation
        if request.company is not None:
            profile.company = request.company
        if request.id_proof_type is not None:
            profile.id_proof_type = request.id_proof_type
        if request.id_proof_number is not None:
            profile.id_proof_number = request.id_proof_number
        if request.address_line1 is not None:
            profile.address_line1 = request.address_line1
        if request.address_line2 is not None:
            profile.address_line2 = request.address_line2
        if request.city is not None:
            profile.city = request.city
        if request.state is not None:
            profile.state = request.state
        if request.pincode is not None:
            profile.pincode = request.pincode
    
    await db.commit()
    # Materialize attributes for serialization (timestamps, etc.)
    updated_user = await load_user_for_response(db, current_user)
    
    logger.info("Profile updated successfully", user_id=str(current_user.id))
    
    return updated_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    logger.info("Password change attempt", user_id=str(current_user.id))
    
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        logger.warning("Password change failed - invalid current password", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    await db.commit()
    
    # Revoke all refresh tokens for security
    stmt = update(RefreshToken).where(RefreshToken.user_id == current_user.id).values(is_revoked=True)
    await db.execute(stmt)
    await db.commit()
    
    logger.info("Password changed successfully", user_id=str(current_user.id))
    
    return MessageResponse(message="Password changed successfully")


@router.get("/.well-known/jwks.json", response_model=JWKSResponse)
async def jwks():
    """Get JSON Web Key Set for token verification"""
    public_key_jwk = security_manager.get_public_key_jwk()
    return JWKSResponse(keys=[public_key_jwk])