import httpx
from typing import Optional
from config import NETTAP_API_URL, NETTAP_ADMIN_USER, NETTAP_ADMIN_PASS, SUB_DOMAIN

_cached_token = None

async def get_admin_token() -> Optional[str]:
    global _cached_token
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{NETTAP_API_URL}/api/auth/login",
                json={"username": NETTAP_ADMIN_USER, "password": NETTAP_ADMIN_PASS}
            )
            if response.status_code == 200:
                _cached_token = response.json().get("access_token")
                return _cached_token
    except:
        pass
    return None

async def create_user(username: str, duration_minutes: int, group_id: Optional[int] = None) -> Optional[dict]:
    token = await get_admin_token()
    if not token:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "username": username,
                "duration_minutes": duration_minutes
            }
            if group_id:
                payload["group_id"] = group_id
                
            response = await client.post(
                f"{NETTAP_API_URL}/api/users/",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                data["sub_url"] = f"{SUB_DOMAIN}/sub/{data['token']}"
                return data
    except:
        pass
    return None

async def block_user(user_id: int) -> bool:
    token = await get_admin_token()
    if not token:
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{NETTAP_API_URL}/api/users/{user_id}/block",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.status_code == 200
    except:
        return False

async def get_user_by_username(username: str) -> Optional[dict]:
    token = await get_admin_token()
    if not token:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NETTAP_API_URL}/api/users/",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user["username"] == username:
                        return user
    except:
        pass
    return None

async def get_all_users() -> Optional[list]:
    token = await get_admin_token()
    if not token:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NETTAP_API_URL}/api/users/",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None

def build_sub_url(token: str) -> str:
    return f"{SUB_DOMAIN}/sub/{token}"

async def get_public_plans() -> Optional[list]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NETTAP_API_URL}/api/plans/public")
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None