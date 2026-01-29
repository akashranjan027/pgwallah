import sys
import os
import asyncio
from sqlalchemy import select

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole, TenantProfile
from app.core.security import get_password_hash

async def seed_users():
    print("🌱 Seeding users...")
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("Creating admin user...")
            admin = User(
                email="admin@example.com",
                hashed_password=get_password_hash("password123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            session.add(admin)
        else:
            print("Admin user already exists.")
            
        # Check if tenant exists
        result = await session.execute(select(User).where(User.email == "tenant@example.com"))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            print("Creating tenant user...")
            tenant = User(
                email="tenant@example.com",
                hashed_password=get_password_hash("password123"),
                full_name="Tenant User",
                role=UserRole.TENANT,
                is_active=True,
                is_verified=True
            )
            session.add(tenant)
            await session.flush() # Flush to get tenant ID
            
            # Create tenant profile
            profile = TenantProfile(
                user_id=tenant.id,
                occupation="Software Engineer",
                company="Tech Corp",
                emergency_contact_name="Emergency Contact",
                emergency_contact_phone="9876543210",
                address_line1="123 Tech Park",
                city="Bangalore",
                state="Karnataka",
                pincode="560100"
            )
            session.add(profile)
        else:
            print("Tenant user already exists.")
            
        await session.commit()
        print("✅ Users seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_users())
