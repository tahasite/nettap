import httpx
import subprocess
from typing import Optional
from sqlalchemy.orm import Session
from app.services.settings_manager import get_setting

def get_telegram_base_url(db: Session) -> str:
    proxy = get_setting(db, "telegram_proxy", "")
    if proxy:
        proxy = proxy.rstrip("/")
        return f"{proxy}/bot"
    return "https://api.telegram.org/bot"

async def test_bot_token(db: Session, token: str = None) -> dict:
    if token is None:
        token = get_setting(db, "bot_token", "")
    
    if not token or len(token) < 20:
        return {"success": False, "error": "Token is empty or invalid"}
    
    base_url = get_telegram_base_url(db)
    url = f"{base_url}{token}/getMe"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            data = response.json()
            
            if data.get("ok"):
                bot_info = data.get("result", {})
                return {
                    "success": True,
                    "bot_id": bot_info.get("id"),
                    "username": bot_info.get("username"),
                    "first_name": bot_info.get("first_name"),
                    "can_join_groups": bot_info.get("can_join_groups"),
                    "can_read_messages": bot_info.get("can_read_all_group_messages"),
                }
            else:
                return {"success": False, "error": data.get("description", "Unknown error")}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout. Check proxy or network."}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def test_proxy(db: Session, proxy_url: str = None) -> dict:
    if proxy_url is None:
        proxy_url = get_setting(db, "telegram_proxy", "")
    
    if not proxy_url:
        return {"success": False, "error": "Proxy URL is empty"}
    
    proxy_url = proxy_url.rstrip("/")
    test_url = f"{proxy_url}/bot123:test/getMe"
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(test_url)
            if response.status_code in [200, 401, 404]:
                return {"success": True, "message": "Proxy is reachable"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Proxy timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def check_bot_in_channel(db: Session, channel: str, token: str = None) -> dict:
    if token is None:
        token = get_setting(db, "bot_token", "")
    
    if not token:
        return {"success": False, "error": "No bot token"}
    
    if not channel.startswith("@"):
        channel = "@" + channel
    
    base_url = get_telegram_base_url(db)
    url = f"{base_url}{token}/getChat"
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params={"chat_id": channel})
            data = response.json()
            
            if data.get("ok"):
                chat = data.get("result", {})
                
                me_url = f"{base_url}{token}/getChatMember"
                me_response = await client.get(me_url, params={"chat_id": channel, "user_id": chat.get("id")})
                
                bot_info_url = f"{base_url}{token}/getMe"
                bot_info_response = await client.get(bot_info_url)
                bot_id = None
                if bot_info_response.status_code == 200:
                    bot_data = bot_info_response.json()
                    if bot_data.get("ok"):
                        bot_id = bot_data.get("result", {}).get("id")
                
                is_admin = False
                if bot_id:
                    member_response = await client.get(me_url, params={"chat_id": channel, "user_id": bot_id})
                    if member_response.status_code == 200:
                        member_data = member_response.json()
                        if member_data.get("ok"):
                            status = member_data.get("result", {}).get("status", "")
                            is_admin = status in ["administrator", "creator"]
                
                return {
                    "success": True,
                    "channel": channel,
                    "title": chat.get("title"),
                    "type": chat.get("type"),
                    "members_count": chat.get("members_count", 0),
                    "bot_is_admin": is_admin
                }
            else:
                return {
                    "success": False,
                    "channel": channel,
                    "error": data.get("description", "Not found")
                }
    except Exception as e:
        return {"success": False, "channel": channel, "error": str(e)}

async def set_webhook(db: Session, webhook_url: str = None, token: str = None) -> dict:
    if token is None:
        token = get_setting(db, "bot_token", "")
    if webhook_url is None:
        webhook_url = get_setting(db, "webhook_url", "")
    
    if not token:
        return {"success": False, "error": "No bot token"}
    if not webhook_url:
        return {"success": False, "error": "No webhook URL"}
    
    full_webhook = f"{webhook_url.rstrip('/')}/{token}"
    
    base_url = get_telegram_base_url(db)
    url = f"{base_url}{token}/setWebhook"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={
                "url": full_webhook,
                "max_connections": 100,
                "allowed_updates": ["message", "callback_query", "my_chat_member"]
            })
            data = response.json()
            
            if data.get("ok"):
                return {"success": True, "webhook_url": full_webhook, "message": data.get("description", "")}
            else:
                return {"success": False, "error": data.get("description", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def delete_webhook(db: Session, token: str = None) -> dict:
    if token is None:
        token = get_setting(db, "bot_token", "")
    
    if not token:
        return {"success": False, "error": "No bot token"}
    
    base_url = get_telegram_base_url(db)
    url = f"{base_url}{token}/deleteWebhook"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={"drop_pending_updates": True})
            data = response.json()
            if data.get("ok"):
                return {"success": True, "message": "Webhook deleted"}
            return {"success": False, "error": data.get("description", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def get_webhook_info(db: Session, token: str = None) -> dict:
    if token is None:
        token = get_setting(db, "bot_token", "")
    
    if not token:
        return {"success": False, "error": "No bot token"}
    
    base_url = get_telegram_base_url(db)
    url = f"{base_url}{token}/getWebhookInfo"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            data = response.json()
            if data.get("ok"):
                return {"success": True, "info": data.get("result", {})}
            return {"success": False, "error": data.get("description", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def restart_bot_service() -> dict:
    try:
        result = subprocess.run(
            ["systemctl", "restart", "nettap-bot"],
            capture_output=True,
            timeout=15,
            text=True
        )
        if result.returncode == 0:
            return {"success": True, "message": "Bot service restarted"}
        else:
            return {"success": False, "error": result.stderr or "Failed to restart"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Restart timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_bot_service_status() -> dict:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "nettap-bot"],
            capture_output=True,
            timeout=5,
            text=True
        )
        status = result.stdout.strip()
        
        enabled_result = subprocess.run(
            ["systemctl", "is-enabled", "nettap-bot"],
            capture_output=True,
            timeout=5,
            text=True
        )
        enabled = enabled_result.stdout.strip()
        
        return {
            "active": status == "active",
            "status": status,
            "enabled": enabled == "enabled"
        }
    except Exception as e:
        return {"active": False, "status": "unknown", "enabled": False, "error": str(e)}

async def full_setup_bot(db: Session) -> dict:
    results = {
        "steps": [],
        "success": True,
        "needs_restart": False
    }
    
    token = get_setting(db, "bot_token", "")
    if not token:
        results["success"] = False
        results["steps"].append({"step": "token_check", "success": False, "error": "No bot token configured"})
        return results
    
    proxy = get_setting(db, "telegram_proxy", "")
    if proxy:
        proxy_result = await test_proxy(db, proxy)
        results["steps"].append({"step": "proxy_test", **proxy_result})
        if not proxy_result["success"]:
            results["success"] = False
            return results
    
    token_result = await test_bot_token(db, token)
    results["steps"].append({"step": "token_test", **token_result})
    if not token_result["success"]:
        results["success"] = False
        return results
    
    results["bot_info"] = token_result
    
    bot_username = token_result.get("username", "")
    if bot_username:
        current_username = get_setting(db, "bot_username", "")
        if current_username != bot_username:
            from app.services.settings_manager import set_setting
            set_setting(db, "bot_username", bot_username)
            results["steps"].append({"step": "username_updated", "success": True, "username": bot_username})
    
    channels = get_setting(db, "force_join_channels", "")
    if channels:
        channel_list = [c.strip() for c in channels.split(",") if c.strip()]
        channel_results = []
        for ch in channel_list:
            ch_result = await check_bot_in_channel(db, ch, token)
            channel_results.append(ch_result)
        results["steps"].append({"step": "channels_check", "channels": channel_results})
    
    webhook_url = get_setting(db, "webhook_url", "")
    if webhook_url:
        webhook_result = await set_webhook(db, webhook_url, token)
        results["steps"].append({"step": "webhook_setup", **webhook_result})
        if not webhook_result["success"]:
            results["success"] = False
    
    results["needs_restart"] = True
    
    return results