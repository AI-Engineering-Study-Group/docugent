"""Database initialization script."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import create_tables, AsyncSessionLocal
from app.models import Role, User, Auth
from app.services.auth_service import auth_service


async def create_default_roles():
    """Create default roles."""
    async with AsyncSessionLocal() as db:
        # Check if roles already exist
        result = await db.execute(select(Role))
        existing_roles = result.scalars().all()
        
        if existing_roles:
            print("Roles already exist, skipping creation")
            return
        
        # Create default roles
        default_roles = [
            {
                "name": "admin",
                "description": "Administrator with full system access",
                "permissions": '{"all": true}',
                "is_active": True
            },
            {
                "name": "moderator", 
                "description": "Moderator with limited administrative access",
                "permissions": '{"users": ["read", "update"], "roles": ["read"]}',
                "is_active": True
            },
            {
                "name": "user",
                "description": "Regular user with basic access",
                "permissions": '{"profile": ["read", "update"]}',
                "is_active": True
            }
        ]
        
        for role_data in default_roles:
            role = Role(**role_data)
            db.add(role)
        
        await db.commit()
        print("Default roles created successfully")


async def create_admin_user():
    """Create default admin user."""
    async with AsyncSessionLocal() as db:
        # Check if admin user already exists
        result = await db.execute(
            select(User).join(Role).where(Role.name == "admin")
        )
        admin_user = result.scalar_one_or_none()
        
        if admin_user:
            print("Admin user already exists, skipping creation")
            return
        
        # Get admin role
        result = await db.execute(select(Role).where(Role.name == "admin"))
        admin_role = result.scalar_one()
        
        # Create admin user
        hashed_password, salt = auth_service.hash_password("admin123!@#")
        
        admin_user = User(
            email="admin@apiconf.com",
            first_name="System",
            last_name="Administrator",
            role_id=admin_role.id,
            is_active=True,
            is_verified=True
        )
        db.add(admin_user)
        await db.flush()  # Get user ID
        
        # Create auth record for admin
        admin_auth = Auth(
            user_id=admin_user.id,
            hashed_password=hashed_password,
            salt=salt
        )
        db.add(admin_auth)
        
        await db.commit()
        print("Admin user created successfully")
        print("Email: admin@apiconf.com")
        print("Password: admin123!@#")
        print("Please change the password after first login!")


async def init_database():
    """Initialize database with tables and default data."""
    print("Creating database tables...")
    await create_tables()
    print("Database tables created successfully")
    
    print("Creating default roles...")
    await create_default_roles()
    
    print("Creating admin user...")
    await create_admin_user()
    
    print("Database initialization completed!")


if __name__ == "__main__":
    asyncio.run(init_database())
