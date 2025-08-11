"""
Test script for authentication system.
Run this after setting up the database and starting the server.
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class AuthTestClient:
    """Test client for authentication endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.tokens: Dict[str, str] = {}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/register",
            json=user_data
        )
        return response.json()
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and store tokens."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            self.tokens["access"] = result["data"]["access_token"]
            self.tokens["refresh"] = result["data"]["refresh_token"]
        
        return result
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        headers = {"Authorization": f"Bearer {self.tokens.get('access')}"}
        response = await self.client.get(
            f"{self.base_url}/api/v1/auth/me",
            headers=headers
        )
        return response.json()
    
    async def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role (admin only)."""
        headers = {"Authorization": f"Bearer {self.tokens.get('access')}"}
        response = await self.client.post(
            f"{self.base_url}/api/v1/roles",
            json=role_data,
            headers=headers
        )
        return response.json()
    
    async def get_roles(self) -> Dict[str, Any]:
        """Get all roles."""
        headers = {"Authorization": f"Bearer {self.tokens.get('access')}"}
        response = await self.client.get(
            f"{self.base_url}/api/v1/roles",
            headers=headers
        )
        return response.json()
    
    async def logout(self) -> Dict[str, Any]:
        """Logout user."""
        headers = {"Authorization": f"Bearer {self.tokens.get('access')}"}
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/logout",
            json={"refresh_token": self.tokens.get("refresh")},
            headers=headers
        )
        
        if response.status_code == 200:
            self.tokens.clear()
        
        return response.json()


async def run_tests():
    """Run authentication tests."""
    client = AuthTestClient()
    
    try:
        print("🧪 Running Authentication System Tests\n")
        
        # Test 1: Admin Login
        print("1️⃣ Testing admin login...")
        login_result = await client.login("admin@apiconf.com", "admin123!@#")
        if login_result.get("success"):
            print("✅ Admin login successful")
        else:
            print(f"❌ Admin login failed: {login_result}")
            return
        
        # Test 2: Get Current User
        print("\n2️⃣ Testing get current user...")
        user_result = await client.get_current_user()
        if user_result.get("success"):
            user = user_result["data"]
            print(f"✅ Current user: {user['first_name']} {user['last_name']} ({user['email']})")
            print(f"   Role: {user['role']['name']}")
        else:
            print(f"❌ Get current user failed: {user_result}")
        
        # Test 3: Get Roles
        print("\n3️⃣ Testing get roles...")
        roles_result = await client.get_roles()
        if roles_result.get("success"):
            roles = roles_result["data"]
            print(f"✅ Found {len(roles)} roles:")
            for role in roles:
                print(f"   - {role['name']}: {role['description']}")
        else:
            print(f"❌ Get roles failed: {roles_result}")
        
        # Test 4: Create New Role
        print("\n4️⃣ Testing create new role...")
        new_role = {
            "name": "test_role",
            "description": "Test role created by test script",
            "permissions": '{"test": ["read", "write"]}',
            "is_active": True
        }
        role_result = await client.create_role(new_role)
        if role_result.get("success"):
            print("✅ New role created successfully")
        else:
            print(f"❌ Create role failed: {role_result}")
        
        # Test 5: Register New User
        print("\n5️⃣ Testing user registration...")
        new_user = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890",
            "role_id": 3  # User role
        }
        register_result = await client.register_user(new_user)
        if register_result.get("success"):
            print("✅ User registration successful")
        else:
            print(f"❌ User registration failed: {register_result}")
        
        # Test 6: Login as New User
        print("\n6️⃣ Testing new user login...")
        user_login_result = await client.login("test@example.com", "TestPass123!")
        if user_login_result.get("success"):
            print("✅ New user login successful")
            
            # Check user permissions
            user_info = await client.get_current_user()
            if user_info.get("success"):
                user = user_info["data"]
                print(f"   User: {user['full_name']} (Role: {user['role']['name']})")
        else:
            print(f"❌ New user login failed: {user_login_result}")
        
        # Test 7: Test Role Permissions (try to create role as regular user)
        print("\n7️⃣ Testing role permissions...")
        forbidden_role = {
            "name": "forbidden_role",
            "description": "This should fail",
        }
        forbidden_result = await client.create_role(forbidden_role)
        if not forbidden_result.get("success") and "403" in str(forbidden_result):
            print("✅ Role permissions working correctly (access denied)")
        else:
            print(f"❌ Role permissions not working: {forbidden_result}")
        
        # Test 8: Logout
        print("\n8️⃣ Testing logout...")
        logout_result = await client.logout()
        if logout_result.get("success"):
            print("✅ Logout successful")
        else:
            print(f"❌ Logout failed: {logout_result}")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    print("Starting authentication tests...")
    print("Make sure the server is running on http://localhost:8000")
    print("And the database is initialized with: python scripts/init_db.py\n")
    
    asyncio.run(run_tests())
