import socket
import time
import unicodedata
import httpx
from typing import Optional
from sqlalchemy.orm import Session
from app.models import ExtractedConfig
from app.services.dns_manager import resolve_hostname, is_ip_address

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
    "AR": "🇦🇷", "CL": "🇨🇱", "CO": "🇨🇴", "PE": "🇵🇪", "VE": "🇻🇪",
    "LT": "🇱🇹", "LV": "🇱🇻", "EE": "🇪🇪", "BG": "🇧🇬", "HR": "🇭🇷",
    "SK": "🇸🇰", "SI": "🇸🇮", "IS": "🇮🇸", "LU": "🇱🇺", "MT": "🇲🇹",
}

NAME_TO_COUNTRY = {
    "usa": "US", "united states": "US", "america": "US", "us": "US",
    "germany": "DE", "german": "DE", "alman": "DE", "berlin": "DE", "frankfurt": "DE", "de": "DE",
    "netherlands": "NL", "amsterdam": "NL", "holland": "NL", "dutch": "NL", "nl": "NL",
    "finland": "FI", "helsinki": "FI", "fi": "FI", "فنلاند": "FI",
    "france": "FR", "paris": "FR", "french": "FR", "fr": "FR", "فرانسه": "FR",
    "britain": "GB", "england": "GB", "london": "GB", "united kingdom": "GB", "gb": "GB", "uk": "GB",
    "turkey": "TR", "istanbul": "TR", "turkish": "TR", "tr": "TR", "ترکیه": "TR",
    "russia": "RU", "moscow": "RU", "russian": "RU", "ru": "RU",
    "japan": "JP", "tokyo": "JP", "japanese": "JP", "jp": "JP",
    "singapore": "SG", "sg": "SG",
    "canada": "CA", "toronto": "CA", "ca": "CA",
    "australia": "AU", "sydney": "AU", "au": "AU",
    "italy": "IT", "rome": "IT", "milan": "IT", "it": "IT",
    "sweden": "SE", "stockholm": "SE", "se": "SE",
    "norway": "NO", "oslo": "NO", "no": "NO",
    "poland": "PL", "warsaw": "PL", "pl": "PL",
    "austria": "AT", "vienna": "AT", "at": "AT",
    "switzerland": "CH", "zurich": "CH", "ch": "CH",
    "spain": "ES", "madrid": "ES", "barcelona": "ES", "es": "ES",
    "uae": "AE", "dubai": "AE", "emirates": "AE", "ae": "AE",
    "india": "IN", "mumbai": "IN", "delhi": "IN", "in": "IN",
    "korea": "KR", "seoul": "KR", "kr": "KR",
    "iran": "IR", "tehran": "IR", "ایران": "IR",
    "brazil": "BR", "sao paulo": "BR", "br": "BR",
    "ukraine": "UA", "kiev": "UA", "kyiv": "UA", "ua": "UA",
    "romania": "RO", "bucharest": "RO", "ro": "RO",
    "czech": "CZ", "prague": "CZ", "cz": "CZ",
    "denmark": "DK", "copenhagen": "DK", "dk": "DK",
    "belgium": "BE", "brussels": "BE", "be": "BE",
    "ireland": "IE", "dublin": "IE", "ie": "IE",
    "portugal": "PT", "lisbon": "PT", "pt": "PT",
    "hungary": "HU", "budapest": "HU", "hu": "HU",
    "greece": "GR", "athens": "GR", "gr": "GR",
    "israel": "IL", "tel aviv": "IL", "il": "IL",
    "hong kong": "HK", "hk": "HK",
    "taiwan": "TW", "taipei": "TW", "tw": "TW",
    "thailand": "TH", "bangkok": "TH", "th": "TH",
    "vietnam": "VN", "hanoi": "VN", "vn": "VN",
    "indonesia": "ID", "jakarta": "ID", "id": "ID",
    "malaysia": "MY", "kuala lumpur": "MY", "my": "MY",
    "philippines": "PH", "manila": "PH", "ph": "PH",
    "saudi": "SA", "riyadh": "SA", "sa": "SA",
    "egypt": "EG", "cairo": "EG", "eg": "EG",
    "south africa": "ZA", "za": "ZA",
    "lithuania": "LT", "vilnius": "LT",
    "latvia": "LV", "riga": "LV",
    "estonia": "EE", "tallinn": "EE",
    "bulgaria": "BG", "sofia": "BG",
    "iceland": "IS", "reykjavik": "IS",
}

def parse_host_from_config(raw_config: str) -> Optional[str]:
    try:
        clean = raw_config.split("#")[0]
        parts = clean.split("@")
        if len(parts) < 2:
            return None
        address_part = parts[1].split("?")[0]
        if ":" in address_part:
            host = address_part.split(":")[0]
        else:
            host = address_part
        return host
    except:
        return None

def parse_port_from_config(raw_config: str) -> int:
    try:
        clean = raw_config.split("#")[0]
        parts = clean.split("@")
        if len(parts) < 2:
            return 443
        address_part = parts[1].split("?")[0]
        if ":" in address_part:
            return int(address_part.split(":")[1])
        return 443
    except:
        return 443

def normalize_text(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize('NFKC', text).lower().strip()

def detect_country_from_name(name: str) -> tuple:
    if not name:
        return "XX", "🌍"
    
    for flag_char in COUNTRY_FLAGS.values():
        if flag_char in name:
            for code, flag in COUNTRY_FLAGS.items():
                if flag == flag_char:
                    return code, flag
                    
    normalized = normalize_text(name)
    
    for keyword, code in NAME_TO_COUNTRY.items():
        if keyword in normalized:
            return code, COUNTRY_FLAGS.get(code, "🌍")
            
    return "XX", "🌍"

def get_country_from_ip_local(ip: str) -> tuple:
    if not ip:
        return "XX", "🌍"
    
    apis = [
        f"https://ipapi.co/{ip}/country/",
        f"https://api.iplocation.net/?ip={ip}",
        f"https://ipwho.is/{ip}?fields=country_code",
    ]
    
    for url in apis:
        try:
            response = httpx.get(url, timeout=4.0)
            if response.status_code == 200:
                text = response.text.strip()
                
                if "ipapi.co" in url:
                    code = text.upper()
                    if len(code) == 2 and code.isalpha():
                        return code, COUNTRY_FLAGS.get(code, "🌍")
                
                elif "iplocation.net" in url:
                    data = response.json()
                    code = data.get("country_code2", "").upper()
                    if len(code) == 2:
                        return code, COUNTRY_FLAGS.get(code, "🌍")
                
                elif "ipwho.is" in url:
                    data = response.json()
                    code = data.get("country_code", "").upper()
                    if len(code) == 2:
                        return code, COUNTRY_FLAGS.get(code, "🌍")
        except:
            continue
            
    return "XX", "🌍"

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

def detect_country_for_config(config: ExtractedConfig) -> tuple:
    code, flag = detect_country_from_name(config.name)
    if code != "XX":
        return code, flag
        
    host = parse_host_from_config(config.raw_config)
    if not host:
        return "XX", "🌍"
        
    if is_ip_address(host):
        ip = host
    else:
        ip = resolve_hostname(host)
        
    if not ip:
        return "XX", "🌍"
        
    return get_country_from_ip_local(ip)

def ping_config(config: ExtractedConfig) -> int:
    host = parse_host_from_config(config.raw_config)
    port = parse_port_from_config(config.raw_config)
    if not host:
        return -1
    return tcp_ping(host, port)

def scan_all_configs(db: Session, do_country: bool = True, do_ping: bool = True) -> dict:
    configs = db.query(ExtractedConfig).all()
    stats = {"total": len(configs), "checked": 0, "working": 0, "broken": 0}
    
    for config in configs:
        if do_country:
            code, flag = detect_country_for_config(config)
            config.country_code = code
            config.country_flag = flag
            
        if do_ping:
            ping = ping_config(config)
            config.ping = ping
            if ping > 0:
                config.is_working = True
                stats["working"] += 1
            else:
                config.is_working = False
                stats["broken"] += 1
                
        stats["checked"] += 1
        db.commit()
        
    return stats