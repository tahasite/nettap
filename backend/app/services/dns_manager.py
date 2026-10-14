import os
import socket
import subprocess
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models import DomainMapping, UserSubscription

BLACKHOLE_IP = "0.0.0.0"
DEFAULT_DNS_DOMAIN = os.getenv("DNS_DOMAIN", "nettap.ir")
DEFAULT_DNS_ZONE_FILE = os.getenv("DNS_ZONE_FILE", "/home/ubuntu/vpn-panel/data/nettap.db")
DEFAULT_DNS_SERVER_IP = os.getenv("DNS_SERVER_IP", "95.38.163.161")

def get_dns_config(db: Session):
    try:
        from app.services.settings_manager import get_setting
        return {
            "domain": get_setting(db, "dns_domain", DEFAULT_DNS_DOMAIN),
            "zone_file": DEFAULT_DNS_ZONE_FILE,
            "server_ip": get_setting(db, "server_ip", DEFAULT_DNS_SERVER_IP)
        }
    except:
        return {
            "domain": DEFAULT_DNS_DOMAIN,
            "zone_file": DEFAULT_DNS_ZONE_FILE,
            "server_ip": DEFAULT_DNS_SERVER_IP
        }

def resolve_hostname(hostname: str) -> Optional[str]:
    try:
        socket.setdefaulttimeout(4)
        return socket.gethostbyname(hostname)
    except Exception:
        return None

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
    except Exception:
        return False

def slugify_username(username: str) -> str:
    result = ""
    for char in username.lower():
        if char.isalnum():
            result += char
        elif char in ['-', '_']:
            result += '-'
    return result[:20] if result else "user"

def build_subdomain(username: str, server_index: int) -> str:
    slug = slugify_username(username)
    return f"srv{server_index}-{slug}"

def rebuild_zone_file(db: Session):
    cfg = get_dns_config(db)
    dns_domain = cfg["domain"]
    dns_zone_file = cfg["zone_file"]
    dns_server_ip = cfg["server_ip"]
    
    serial = int(datetime.utcnow().timestamp())
    
    lines = [
        f"$ORIGIN {dns_domain}.",
        f"@   IN  SOA ns1.{dns_domain}. admin.{dns_domain}. (",
        f"        {serial}",
        f"        7200",
        f"        3600",
        f"        1209600",
        f"        60",
        f"        )",
        f"@   IN  NS  ns1.{dns_domain}.",
        f"@   IN  NS  ns2.{dns_domain}.",
        f"ns1 IN  A   {dns_server_ip}",
        f"ns2 IN  A   {dns_server_ip}",
        ""
    ]
    
    all_mappings = db.query(DomainMapping).all()
    for mapping in all_mappings:
        if not mapping.resolved_ip:
            continue
        
        user = db.query(UserSubscription).filter(UserSubscription.id == mapping.user_id).first()
        if not user:
            continue
        
        should_blackhole = False
        if not mapping.is_active:
            should_blackhole = True
        if user.is_blocked:
            should_blackhole = True
        if user.expire_date and user.expire_date < datetime.utcnow():
            should_blackhole = True
        
        ip_to_use = BLACKHOLE_IP if should_blackhole else mapping.resolved_ip
        lines.append(f"{mapping.subdomain}   30  IN  A   {ip_to_use}")
    
    content = "\n".join(lines) + "\n"
    with open(dns_zone_file, 'w') as f:
        f.write(content)
    
    reload_coredns()

def reload_coredns():
    try:
        subprocess.run(
            ["systemctl", "reload", "coredns"],
            check=False, capture_output=True, timeout=5
        )
    except:
        try:
            subprocess.run(
                ["systemctl", "restart", "coredns"],
                check=False, capture_output=True, timeout=5
            )
        except:
            pass

def get_or_create_mapping(db: Session, user: UserSubscription, original_host: str, resolved_ip: str, server_index: int) -> Optional[DomainMapping]:
    existing = db.query(DomainMapping).filter(
        DomainMapping.user_id == user.id,
        DomainMapping.original_host == original_host
    ).first()
    
    if existing:
        existing.last_used = datetime.utcnow()
        if resolved_ip and existing.resolved_ip != resolved_ip:
            existing.resolved_ip = resolved_ip
            db.commit()
        return existing
        
    if not resolved_ip:
        return None
    
    subdomain = build_subdomain(user.username, server_index)
    counter = 1
    original_subdomain = subdomain
    while db.query(DomainMapping).filter(DomainMapping.subdomain == subdomain).first():
        subdomain = f"{original_subdomain}-{counter}"
        counter += 1
    
    new_mapping = DomainMapping(
        user_id=user.id, subdomain=subdomain, original_host=original_host,
        resolved_ip=resolved_ip, is_active=True,
        last_ip_check=datetime.utcnow(), last_used=datetime.utcnow()
    )
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    return new_mapping

def block_user_mappings(db: Session, user_id: int):
    db.query(DomainMapping).filter(DomainMapping.user_id == user_id).update({"is_active": False})
    db.commit()
    rebuild_zone_file(db)

def unblock_user_mappings(db: Session, user_id: int):
    db.query(DomainMapping).filter(DomainMapping.user_id == user_id).update({"is_active": True})
    db.commit()
    rebuild_zone_file(db)

def delete_user_mappings(db: Session, user_id: int):
    mappings = db.query(DomainMapping).filter(DomainMapping.user_id == user_id).all()
    for m in mappings:
        m.is_active = False
        m.resolved_ip = BLACKHOLE_IP
    db.commit()
    rebuild_zone_file(db)
    db.query(DomainMapping).filter(DomainMapping.user_id == user_id).delete()
    db.commit()

def refresh_all_ips(db: Session):
    return 0

def cleanup_stale_mappings(db: Session, days_unused: int = 7):
    threshold = datetime.utcnow() - timedelta(days=days_unused)
    stale = db.query(DomainMapping).filter(DomainMapping.last_used < threshold).all()
    count = len(stale)
    for mapping in stale:
        db.delete(mapping)
    db.commit()
    if count > 0:
        rebuild_zone_file(db)
    return count

def cleanup_expired_user_mappings(db: Session):
    return 0