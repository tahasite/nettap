import base64
import socket
import time
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SellerSubscription, ExtractedConfig

def decode_base64_sub(content: str) -> str:
    content = content.strip()
    try:
        missing_padding = len(content) % 4
        if missing_padding:
            content += '=' * (4 - missing_padding)
        return base64.b64decode(content).decode('utf-8')
    except:
        return content

def is_fake_config(config: str) -> bool:
    fake_indicators = ["127.0.0.1:1080", "0.0.0.0:0", "127.0.0.1:0", "127.0.0.1:1", "127.0.0.1:2"]
    for indicator in fake_indicators:
        if indicator in config:
            return True
    
    from urllib.parse import unquote
    name = ""
    if "#" in config:
        name = unquote(config.split("#")[-1]).lower()
    
    info_indicators = ["حجم", "باقی", "تاریخ", "انقضا", "مانده", "اشتراک", "نام اشتراک", "traffic", "expire", "remaining"]
    for indicator in info_indicators:
        if indicator in name:
            return True
    return False

def parse_host(config: str) -> str:
    try:
        clean = config.split("#")[0]
        parts = clean.split("@")
        if len(parts) < 2:
            return ""
        address_part = parts[1].split("?")[0]
        if ":" in address_part:
            return address_part.split(":")[0]
        return address_part
    except:
        return ""

def parse_port(config: str) -> int:
    try:
        clean = config.split("#")[0]
        parts = clean.split("@")
        if len(parts) < 2:
            return 443
        address_part = parts[1].split("?")[0]
        if ":" in address_part:
            return int(address_part.split(":")[1])
        return 443
    except:
        return 443

def is_ip_address(value: str) -> bool:
    try:
        parts = value.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            num = int(part)
            if num < 0 or num > 255:
                return False
        return True
    except:
        return False

def resolve_hostname(hostname: str) -> str:
    try:
        socket.setdefaulttimeout(4)
        return socket.gethostbyname(hostname)
    except:
        return ""

def tcp_ping(host: str, port: int, timeout: float = 3.0) -> int:
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        elapsed = int((time.time() - start) * 1000)
        if result == 0:
            return elapsed
        return -1
    except:
        return -1

COUNTRY_FLAGS = {
    "US": "🇺🇸", "DE": "🇩🇪", "NL": "🇳🇱", "FI": "🇫🇮", "FR": "🇫🇷",
    "GB": "🇬🇧", "TR": "🇹🇷", "RU": "🇷🇺", "JP": "🇯🇵", "SG": "🇸🇬",
    "CA": "🇨🇦", "AU": "🇦🇺", "IT": "🇮🇹", "SE": "🇸🇪", "NO": "🇳🇴",
    "PL": "🇵🇱", "AT": "🇦🇹", "CH": "🇨🇭", "ES": "🇪🇸", "AE": "🇦🇪",
    "IN": "🇮🇳", "KR": "🇰🇷", "IR": "🇮🇷", "BR": "🇧🇷", "MX": "🇲🇽",
    "UA": "🇺🇦", "RO": "🇷🇴", "CZ": "🇨🇿", "DK": "🇩🇰", "BE": "🇧🇪",
    "IE": "🇮🇪", "PT": "🇵🇹", "HU": "🇭🇺", "GR": "🇬🇷", "IL": "🇮🇱",
    "HK": "🇭🇰", "TW": "🇹🇼", "TH": "🇹🇭", "VN": "🇻🇳", "ID": "🇮🇩",
    "MY": "🇲🇾", "PH": "🇵🇭", "SA": "🇸🇦", "EG": "🇪🇬", "ZA": "🇿🇦",
    "AR": "🇦🇷", "CL": "🇨🇱", "CO": "🇨🇴", "LT": "🇱🇹", "LV": "🇱🇻",
    "EE": "🇪🇪", "BG": "🇧🇬", "HR": "🇭🇷", "SK": "🇸🇰", "SI": "🇸🇮",
}

NAME_COUNTRY_MAP = {
    "usa": "US", "united states": "US", "america": "US",
    "germany": "DE", "german": "DE", "alman": "DE", "berlin": "DE", "frankfurt": "DE",
    "netherlands": "NL", "amsterdam": "NL", "holland": "NL", "dutch": "NL",
    "finland": "FI", "helsinki": "FI", "فنلاند": "FI",
    "france": "FR", "paris": "FR", "فرانسه": "FR",
    "britain": "GB", "england": "GB", "london": "GB", "united kingdom": "GB",
    "turkey": "TR", "istanbul": "TR", "ترکیه": "TR",
    "russia": "RU", "moscow": "RU",
    "japan": "JP", "tokyo": "JP",
    "singapore": "SG",
    "canada": "CA", "toronto": "CA",
    "australia": "AU", "sydney": "AU",
    "italy": "IT", "rome": "IT",
    "sweden": "SE", "stockholm": "SE",
    "norway": "NO", "oslo": "NO",
    "poland": "PL", "warsaw": "PL",
    "austria": "AT", "vienna": "AT",
    "switzerland": "CH", "zurich": "CH",
    "spain": "ES", "madrid": "ES",
    "uae": "AE", "dubai": "AE",
    "india": "IN",
    "korea": "KR",
    "iran": "IR", "ایران": "IR",
    "brazil": "BR",
}

def detect_country_from_name(name: str) -> tuple:
    if not name:
        return "XX", "🌍"
    
    import unicodedata
    normalized = unicodedata.normalize('NFKC', name).lower().strip()
    
    for flag_char in COUNTRY_FLAGS.values():
        if flag_char in name:
            for code, flag in COUNTRY_FLAGS.items():
                if flag == flag_char:
                    return code, flag
    
    for keyword, code in NAME_COUNTRY_MAP.items():
        if keyword in normalized:
            return code, COUNTRY_FLAGS.get(code, "🌍")
    
    return "XX", "🌍"

def detect_country_from_ip(ip: str) -> tuple:
    if not ip:
        return "XX", "🌍"
    
    apis = [
        f"https://ipwho.is/{ip}?fields=country_code",
        f"https://ipapi.co/{ip}/country/",
    ]
    
    for url in apis:
        try:
            response = httpx.get(url, timeout=4.0)
            if response.status_code == 200:
                if "ipwho.is" in url:
                    data = response.json()
                    code = data.get("country_code", "").upper()
                else:
                    code = response.text.strip().upper()
                
                if len(code) == 2 and code.isalpha():
                    return code, COUNTRY_FLAGS.get(code, "🌍")
        except:
            continue
    return "XX", "🌍"

def parse_config_name(config: str) -> tuple:
    config = config.strip()
    protocol = "unknown"
    if config.startswith("vless://"):
        protocol = "vless"
    elif config.startswith("vmess://"):
        protocol = "vmess"
    elif config.startswith("ss://"):
        protocol = "ss"
    elif config.startswith("trojan://"):
        protocol = "trojan"
    
    name = "Connection"
    if "#" in config:
        try:
            name = config.split("#")[-1]
            from urllib.parse import unquote
            name = unquote(name)
        except:
            pass
    return protocol, name

def enrich_config(config: ExtractedConfig):
    code, flag = detect_country_from_name(config.name)
    
    if code == "XX" and config.resolved_ip:
        code, flag = detect_country_from_ip(config.resolved_ip)
    
    config.country_code = code
    config.country_flag = flag
    
    if config.resolved_ip:
        host = config.resolved_ip
        port = parse_port(config.raw_config)
        ping = tcp_ping(host, port, timeout=2.5)
        config.ping = ping
        config.is_working = ping > 0

def run_scraper(db: Session, auto_scan: bool = True):
    sellers = db.query(SellerSubscription).filter(SellerSubscription.is_active == True).all()
    if not sellers:
        return
    
    pinned_configs = db.query(ExtractedConfig).filter(ExtractedConfig.is_pinned == True).all()
    pinned_raw = {c.raw_config for c in pinned_configs}
    
    db.query(ExtractedConfig).filter(ExtractedConfig.is_pinned == False).delete()
    db.commit()
    
    headers = {"User-Agent": "v2ray/1.0"}
    new_configs = []
    
    with httpx.Client(headers=headers, timeout=15.0, follow_redirects=True) as client:
        for seller in sellers:
            try:
                response = client.get(seller.url)
                if response.status_code != 200:
                    seller.is_active = False
                    db.commit()
                    continue
                
                raw_data = response.text
                decoded_data = decode_base64_sub(raw_data)
                lines = decoded_data.splitlines()
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if not any(line.startswith(p) for p in ["vless://", "vmess://", "ss://", "trojan://"]):
                        continue
                    
                    if is_fake_config(line):
                        continue
                    
                    if line in pinned_raw:
                        continue
                    
                    host = parse_host(line)
                    if not host:
                        continue
                        
                    resolved_ip = host if is_ip_address(host) else resolve_hostname(host)
                    if not resolved_ip:
                        continue
                    
                    protocol, parsed_name = parse_config_name(line)
                    new_config = ExtractedConfig(
                        seller_sub_id=seller.id,
                        raw_config=line,
                        name=parsed_name,
                        protocol=protocol,
                        resolved_ip=resolved_ip,
                        country_code="XX",
                        country_flag="🌍",
                        is_working=True,
                        is_pinned=False,
                        last_checked=datetime.utcnow()
                    )
                    db.add(new_config)
                    new_configs.append(new_config)
                
                seller.last_updated = datetime.utcnow()
                seller.is_active = True
                db.commit()
                
            except Exception:
                seller.is_active = False
                db.commit()
    
    if auto_scan and new_configs:
        all_fresh = db.query(ExtractedConfig).filter(ExtractedConfig.is_pinned == False).all()
        for config in all_fresh:
            enrich_config(config)
        db.commit()