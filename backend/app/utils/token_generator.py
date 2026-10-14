import base64
import secrets
import hashlib
from datetime import datetime

def generate_secure_token(user_id: int = None) -> str:
    timestamp = int(datetime.utcnow().timestamp())
    user_part = user_id if user_id else secrets.randbelow(99999)
    
    data_str = f"v3,{user_part},{timestamp}"
    data_b64 = base64.urlsafe_b64encode(data_str.encode()).decode().rstrip('=')
    
    signature_bytes = secrets.token_bytes(32)
    signature_b64 = base64.urlsafe_b64encode(signature_bytes).decode().rstrip('=')
    
    return f"{data_b64}.{signature_b64}"