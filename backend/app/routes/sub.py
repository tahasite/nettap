import os
import base64
import json
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
from fastapi import APIRouter, Depends, Header, Request, BackgroundTasks
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UserSubscription, ExtractedConfig, ConfigGroup
from app.services.dns_manager import get_or_create_mapping, rebuild_zone_file
from app.services.settings_manager import get_setting

router = APIRouter(prefix="/sub", tags=["subscription"])

def parse_host_and_port(config: str) -> tuple:
    try:
        clean = config.split("#")[0]
        parts = clean.split("@")
        if len(parts) < 2:
            return "", "", clean
        address_part = parts[1].split("?")[0]
        if ":" in address_part:
            host, port = address_part.split(":")
        else:
            host, port = address_part, "443"
        return host, port, clean
    except:
        return "", "", config

def get_user_configs(db: Session, user: UserSubscription) -> list:
    if user.group_id:
        group = db.query(ConfigGroup).filter(ConfigGroup.id == user.group_id).first()
        if group and group.configs:
            return [c for c in group.configs if c.is_working]
    
    pinned = db.query(ExtractedConfig).filter(
        ExtractedConfig.is_working == True,
        ExtractedConfig.is_pinned == True
    ).all()
    
    if pinned:
        return pinned
    
    return db.query(ExtractedConfig).filter(ExtractedConfig.is_working == True).all()

def build_info_config(user: UserSubscription, status_text: str, db: Session) -> dict:
    brand_name = get_setting(db, "brand_name", "NETtap")
    
    expire_text = "∞"
    if user.expire_date:
        delta = user.expire_date - datetime.utcnow()
        total_minutes = int(delta.total_seconds() / 60)
        if total_minutes > 0:
            if total_minutes >= 1440:
                expire_text = f"{total_minutes // 1440}d"
            elif total_minutes >= 60:
                expire_text = f"{total_minutes // 60}h"
            else:
                expire_text = f"{total_minutes}m"
        else:
            expire_text = "Expired"
    elif user.first_use is None:
        expire_text = "Ready"
    
    info_name = f"ℹ️ {brand_name} • {status_text} • ⏱{expire_text}"
    info_uuid = "11111111-1111-1111-1111-111111111111"
    
    return {
        "url": f"vless://{info_uuid}@1.1.1.1:443?encryption=none&security=tls&type=tcp&sni=info.local#{quote(info_name)}",
        "name": info_name,
        "flag": "ℹ️",
        "code": "INFO",
        "ping": -1,
        "is_info": True
    }

def build_configs_list(db: Session, user: UserSubscription, expired: bool = False) -> tuple:
    brand_name = get_setting(db, "brand_name", "NETtap")
    dns_domain = get_setting(db, "dns_domain", "nettap.ir")
    
    if expired:
        expired_msg = f"❌ {brand_name} • Expired • Renew Please"
        return ([{
            "url": f"vless://11111111-1111-1111-1111-111111111111@1.1.1.1:443?encryption=none&security=none&type=tcp#{quote(expired_msg)}",
            "name": expired_msg,
            "flag": "❌",
            "code": "XX",
            "ping": -1,
            "is_info": True
        }], False)
    
    source_configs = get_user_configs(db, user)
    processed_configs = []
    zone_needs_rebuild = False
    
    status_text = "Active"
    if user.is_blocked:
        status_text = "Blocked"
    elif not user.is_active:
        status_text = "Inactive"
    elif user.first_use is None:
        status_text = "Ready"
    
    info_config = build_info_config(user, status_text, db)
    processed_configs.append(info_config)
    
    for idx, config in enumerate(source_configs, 1):
        raw = config.raw_config
        host, port, clean_config = parse_host_and_port(raw)
        if not host:
            continue
            
        mapping = get_or_create_mapping(db, user, host, config.resolved_ip, idx)
        if not mapping:
            continue
            
        zone_needs_rebuild = True
        mapped_host = f"{mapping.subdomain}.{dns_domain}"
        new_config_base = clean_config.replace(f"@{host}:{port}", f"@{mapped_host}:{port}").replace(f"@{host}", f"@{mapped_host}")
        
        flag = config.country_flag or "🌍"
        code = config.country_code or "XX"
        new_name = f"{flag} {code} | {brand_name} - S{idx}"
        
        final_config = f"{new_config_base}#{quote(new_name)}"
        processed_configs.append({
            "url": final_config,
            "name": f"Server {idx}",
            "flag": flag,
            "code": code,
            "ping": config.ping if config.ping > 0 else 0,
            "is_info": False
        })
        
    return processed_configs, zone_needs_rebuild

def is_browser_request(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    user_agent = request.headers.get("user-agent", "").lower()
    
    if "text/html" not in accept:
        return False
        
    client_keywords = [
        "v2ray", "clash", "hiddify", "sing-box", "shadowrocket", "nekobox", 
        "streisand", "loon", "surge", "happ", "npv", "quantumult", "stash", 
        "sfa", "sfi", "foxray", "karing", "v2box", "bifrost"
    ]
    
    if any(client in user_agent for client in client_keywords):
        return False
        
    return True

def check_and_activate_user(user: UserSubscription, db: Session) -> bool:
    now = datetime.utcnow()
    if user.first_use is None:
        user.first_use = now
        user.expire_date = now + timedelta(minutes=user.duration_minutes)
        db.commit()
        db.refresh(user)
        
    if user.expire_date and user.expire_date < now:
        user.is_active = False
        db.commit()
        return True
        
    return False

def detect_lang_from_ip(request: Request) -> str:
    try:
        forwarded = request.headers.get("x-forwarded-for", "")
        real_ip = request.headers.get("x-real-ip", "")
        ip = None
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        elif real_ip:
            ip = real_ip
        else:
            ip = request.client.host if request.client else None
        
        if not ip or ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
            return "en"
        
        import httpx
        apis = [
            f"https://ipwho.is/{ip}?fields=country_code",
            f"https://ipapi.co/{ip}/country/",
        ]
        
        for url in apis:
            try:
                response = httpx.get(url, timeout=3.0)
                if response.status_code == 200:
                    if "ipwho.is" in url:
                        data = response.json()
                        code = data.get("country_code", "").upper()
                    else:
                        code = response.text.strip().upper()
                    
                    if code == "IR":
                        return "fa"
                    if code == "RU":
                        return "ru"
                    if len(code) == 2:
                        return "en"
            except:
                continue
    except:
        pass
    return "en"

def render_html_page(user: UserSubscription, configs_data: list, sub_url: str, lang: str, db: Session) -> str:
    brand_name = get_setting(db, "brand_name", "NETtap")
    parent_brand = get_setting(db, "parent_brand", "TahaSite")
    company_website = get_setting(db, "company_website", "https://tahasite.ir")
    primary_color = get_setting(db, "primary_color", "#6366f1")
    secondary_color = get_setting(db, "secondary_color", "#8b5cf6")
    
    is_active_status = user.is_active and not user.is_blocked
    first_use_iso = user.first_use.isoformat() + "Z" if user.first_use else ""
    expire_date_iso = user.expire_date.isoformat() + "Z" if user.expire_date else ""
    
    display_configs = [c for c in configs_data if not c.get("is_info")]
    
    user_data = {
        "username": user.username,
        "is_active": is_active_status,
        "is_blocked": user.is_blocked,
        "first_use": first_use_iso,
        "expire_date": expire_date_iso,
        "duration_minutes": user.duration_minutes,
        "config_count": len(display_configs),
        "sub_url": sub_url
    }
    
    configs_json = json.dumps(display_configs)
    user_json = json.dumps(user_data)
    
    return f'''<!DOCTYPE html>
<html lang="{lang}" id="html-root">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="theme-color" content="#0f172a" id="meta-theme">
    <title>{brand_name} | {user.username}</title>
    <link rel="stylesheet" href="/admin/assets/css/style.css">
    <link rel="stylesheet" href="/admin/assets/vendor/fontawesome/css/all.min.css">
    <script src="/admin/assets/vendor/tailwindcss.js"></script>
    <script src="/admin/assets/vendor/qrcode.min.js"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{ extend: {{ fontFamily: {{ sans: ['Vazir', 'sans-serif'] }} }} }}
        }}
    </script>
    <style>
        :root {{
            --primary: {primary_color};
            --secondary: {secondary_color};
        }}
        * {{ -webkit-tap-highlight-color: transparent; }}
        body {{
            transition: background 0.5s ease, color 0.3s ease;
            background: radial-gradient(ellipse at top, #1e1b4b 0%, #0f172a 40%, #020617 100%);
            min-height: 100vh;
            position: relative;
        }}
        body.light-mode {{
            background: radial-gradient(ellipse at top, #e0e7ff 0%, #f1f5f9 40%, #ffffff 100%);
            color: #0f172a;
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
            50% {{ transform: translateY(-20px) rotate(180deg); }}
        }}
        @keyframes pulse-glow {{
            0%, 100% {{ box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); }}
            50% {{ box-shadow: 0 0 40px rgba(139, 92, 246, 0.6); }}
        }}
        @keyframes slide-up {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes scale-in {{
            from {{ opacity: 0; transform: scale(0.9); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        @keyframes fade-in {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        .animate-float {{ animation: float 6s ease-in-out infinite; }}
        .animate-pulse-glow {{ animation: pulse-glow 3s ease-in-out infinite; }}
        .animate-slide-up {{ animation: slide-up 0.6s ease-out forwards; opacity: 0; }}
        .animate-scale-in {{ animation: scale-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards; }}
        .animate-fade-in {{ animation: fade-in 0.5s ease-out forwards; }}
        .glass-card {{
            background: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(148, 163, 184, 0.15);
            transition: all 0.3s ease;
        }}
        body.light-mode .glass-card {{
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
        }}
        .glass-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(99, 102, 241, 0.4);
        }}
        .config-item {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(51, 65, 85, 0.5);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        body.light-mode .config-item {{
            background: rgba(248, 250, 252, 0.9);
            border: 1px solid rgba(203, 213, 225, 0.7);
        }}
        .config-item:hover {{
            transform: translateX(5px);
            border-color: rgba(99, 102, 241, 0.5);
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
        }}
        [dir="ltr"] .config-item:hover {{ transform: translateX(-5px); }}
        .progress-ring {{ transform: rotate(-90deg); }}
        .progress-ring circle {{ transition: stroke-dashoffset 1s ease-out; }}
        .btn-primary {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            border: none;
            cursor: pointer;
        }}
        .btn-primary::before {{ content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); transition: left 0.6s; }}
        .btn-primary:hover::before {{ left: 100%; }}
        .btn-primary:hover {{
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
            transform: translateY(-1px);
        }}
        .btn-primary:active {{ transform: translateY(0) scale(0.98); }}
        .floating-orb {{
            position: fixed;
            border-radius: 50%;
            filter: blur(60px);
            opacity: 0.4;
            pointer-events: none;
            z-index: 0;
        }}
        body.light-mode .floating-orb {{ opacity: 0.15; }}
        .text-primary {{ color: #f1f5f9; }}
        .text-secondary {{ color: #94a3b8; }}
        body.light-mode .text-primary {{ color: #0f172a; }}
        body.light-mode .text-secondary {{ color: #64748b; }}
        .divider {{ border-color: rgba(148, 163, 184, 0.15); }}
        body.light-mode .divider {{ border-color: rgba(203, 213, 225, 0.5); }}
        .input-field {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(51, 65, 85, 0.5);
            color: #f1f5f9;
        }}
        body.light-mode .input-field {{
            background: rgba(248, 250, 252, 0.9);
            border: 1px solid rgba(203, 213, 225, 0.7);
            color: #0f172a;
        }}
        .icon-btn {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(51, 65, 85, 0.5);
            transition: all 0.3s ease;
            color: #f1f5f9;
            cursor: pointer;
        }}
        body.light-mode .icon-btn {{
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(203, 213, 225, 0.7);
            color: #0f172a;
        }}
        .icon-btn:hover {{
            transform: scale(1.05);
            border-color: var(--primary);
            color: var(--primary);
        }}
        .scroll-smooth::-webkit-scrollbar {{ width: 6px; }}
        .scroll-smooth::-webkit-scrollbar-track {{ background: transparent; }}
        .scroll-smooth::-webkit-scrollbar-thumb {{
            background: rgba(99, 102, 241, 0.4);
            border-radius: 3px;
        }}
        .lang-dropdown {{
            position: absolute;
            top: calc(100% + 8px);
            left: 0;
            min-width: 170px;
            z-index: 9999;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }}
        body.light-mode .lang-dropdown {{
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(203, 213, 225, 0.5);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        }}
        .lang-menu-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            width: 100%;
            padding: 12px 16px;
            font-size: 14px;
            text-align: right;
            border: none;
            background: transparent;
            cursor: pointer;
            transition: all 0.2s ease;
            color: inherit;
        }}
        [dir="ltr"] .lang-menu-item {{ text-align: left; }}
        .lang-menu-item:hover {{ background: linear-gradient(90deg, rgba(99, 102, 241, 0.2), transparent); }}
        .lang-menu-item.active {{
            background: rgba(99, 102, 241, 0.15);
            color: #a5b4fc;
            font-weight: 600;
        }}
        .ping-dot {{
            display: inline-block;
            width: 8px; height: 8px;
            border-radius: 50%;
            margin: 0 4px;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .ping-good {{ background: #10b981; box-shadow: 0 0 8px #10b981; }}
        .ping-medium {{ background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }}
        .ping-slow {{ background: #ef4444; box-shadow: 0 0 8px #ef4444; }}
        .ping-none {{ background: #64748b; }}
        .fa-icon-gradient {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        @media (max-width: 640px) {{
            .desktop-only {{ display: none; }}
        }}
        .status-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        .status-dot.pulse {{ animation: pulse 2s infinite; }}
        .config-flag {{ font-size: 32px; line-height: 1; }}
        .header-container {{ position: relative; z-index: 100; }}
        .lang-container {{ position: relative; z-index: 200; }}
        .brand-logo {{
            background: linear-gradient(135deg, var(--primary), var(--secondary), #ec4899);
        }}
        .brand-title {{
            background: linear-gradient(135deg, var(--primary), var(--secondary), #ec4899);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
    </style>
</head>
<body class="min-h-screen p-3 sm:p-4 text-primary" id="body-root">
    
    <div class="floating-orb animate-float" style="width: 300px; height: 300px; background: {primary_color}; top: 5%; right: 5%; animation-delay: 0s;"></div>
    <div class="floating-orb animate-float" style="width: 250px; height: 250px; background: {secondary_color}; top: 40%; left: 5%; animation-delay: 2s;"></div>
    <div class="floating-orb animate-float" style="width: 200px; height: 200px; background: #ec4899; bottom: 10%; right: 20%; animation-delay: 4s;"></div>
    
    <div class="max-w-3xl mx-auto py-3 sm:py-6 relative">
        
        <div class="header-container flex justify-between items-center mb-6 animate-fade-in">
            <div class="flex items-center gap-2">
                <button id="theme-toggle" type="button" class="icon-btn w-11 h-11 rounded-2xl flex items-center justify-center text-lg" aria-label="Toggle Theme">
                    <i id="theme-icon" class="fas fa-moon"></i>
                </button>
                
                <div class="lang-container">
                    <button id="lang-btn" type="button" class="icon-btn h-11 px-4 rounded-2xl flex items-center gap-2 text-sm font-medium">
                        <i class="fas fa-globe"></i>
                        <span id="current-lang-name">EN</span>
                        <i class="fas fa-chevron-down text-xs opacity-60"></i>
                    </button>
                    <div id="lang-menu" class="lang-dropdown hidden animate-scale-in">
                        <button type="button" onclick="setLang('en')" class="lang-menu-item" data-lang="en">
                            <span class="text-lg">🇬🇧</span>
                            <span class="flex-1">English</span>
                            <i class="fas fa-check text-indigo-400 hidden check-icon"></i>
                        </button>
                        <button type="button" onclick="setLang('fa')" class="lang-menu-item" data-lang="fa">
                            <span class="text-lg">🇮🇷</span>
                            <span class="flex-1">فارسی</span>
                            <i class="fas fa-check text-indigo-400 hidden check-icon"></i>
                        </button>
                        <button type="button" onclick="setLang('ru')" class="lang-menu-item" data-lang="ru">
                            <span class="text-lg">🇷🇺</span>
                            <span class="flex-1">Русский</span>
                            <i class="fas fa-check text-indigo-400 hidden check-icon"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="text-xs opacity-60 hidden sm:flex items-center gap-2">
                <i class="fas fa-shield-alt fa-icon-gradient"></i>
                <span data-i18n="powered_by"></span>
            </div>
        </div>

        <div class="text-center mb-8 animate-slide-up" style="animation-delay: 0.1s;">
            <div class="w-20 h-20 brand-logo rounded-3xl flex items-center justify-center text-white text-3xl mx-auto mb-4 shadow-2xl animate-pulse-glow">
                <i class="fas fa-shield-halved"></i>
            </div>
            <h1 class="text-3xl sm:text-4xl font-bold brand-title">
                {brand_name}
            </h1>
            <p class="text-sm opacity-70 mt-2" data-i18n="subtitle"></p>
        </div>

        <div class="glass-card rounded-3xl p-5 sm:p-6 mb-5 animate-slide-up" style="animation-delay: 0.2s;">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-5">
                <div class="flex items-center gap-3">
                    <div class="w-12 h-12 brand-logo rounded-2xl flex items-center justify-center text-white">
                        <i class="fas fa-user text-lg"></i>
                    </div>
                    <div>
                        <div class="text-xs opacity-60 mb-0.5" data-i18n="username"></div>
                        <div class="text-lg sm:text-xl font-bold">{user.username}</div>
                    </div>
                </div>
                <span id="status-badge" class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold"></span>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <div class="rounded-2xl p-4 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                        <i class="fas fa-infinity text-lg"></i>
                    </div>
                    <div>
                        <div class="text-xs opacity-70" data-i18n="volume"></div>
                        <div class="text-sm font-bold text-indigo-400" data-i18n="unlimited"></div>
                    </div>
                </div>
                
                <div class="rounded-2xl p-3 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 flex items-center gap-3">
                    <div class="relative w-12 h-12 flex-shrink-0">
                        <svg class="progress-ring w-12 h-12" viewBox="0 0 40 40">
                            <circle cx="20" cy="20" r="16" fill="none" stroke="rgba(148, 163, 184, 0.2)" stroke-width="3"/>
                            <circle id="progress-circle" cx="20" cy="20" r="16" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-dasharray="100.53" stroke-dashoffset="100.53"/>
                        </svg>
                        <div class="absolute inset-0 flex items-center justify-center text-xs font-bold text-emerald-400" id="days-display-val">—</div>
                    </div>
                    <div class="min-w-0">
                        <div class="text-xs opacity-70" data-i18n="time_remaining"></div>
                        <div class="text-sm font-bold text-emerald-400"><span id="days-unit-val" data-i18n="days"></span></div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4 pt-4 border-t divider text-xs opacity-60 flex items-center gap-2">
                <i class="far fa-calendar-alt"></i>
                <span data-i18n="first_use"></span>:
                <span id="first-use-text" class="opacity-80">—</span>
            </div>
        </div>

        <div class="glass-card rounded-3xl p-5 sm:p-6 mb-5 animate-slide-up" style="animation-delay: 0.3s;">
            <div class="flex items-center gap-2 mb-3">
                <i class="fas fa-link fa-icon-gradient"></i>
                <div class="text-sm font-medium" data-i18n="sub_link"></div>
            </div>
            
            <div class="flex flex-col sm:flex-row gap-2 mb-4">
                <input type="text" value="{sub_url}" readonly 
                    class="input-field flex-1 rounded-xl px-4 py-3 text-xs font-mono focus:outline-none focus:border-indigo-500 transition-all min-w-0"
                    id="sub-link" dir="ltr">
                <div class="grid grid-cols-2 sm:flex gap-2">
                    <button type="button" onclick="copySubLink()" class="btn-primary text-white text-sm rounded-xl px-4 py-3 font-medium flex items-center justify-center gap-2">
                        <i class="far fa-copy"></i><span data-i18n="copy"></span>
                    </button>
                    <button type="button" onclick="showQR(document.getElementById('sub-link').value, 'Subscription Link')" 
                        class="icon-btn rounded-xl px-4 py-3 text-sm font-medium flex items-center justify-center gap-2">
                        <i class="fas fa-qrcode"></i><span>QR</span>
                    </button>
                </div>
            </div>
            
            <div class="text-xs opacity-60 leading-relaxed flex items-start gap-2">
                <i class="fas fa-lightbulb text-amber-400 mt-0.5"></i>
                <span data-i18n="add_hint"></span>
            </div>
        </div>

        <div class="glass-card rounded-3xl p-5 sm:p-6 mb-6 animate-slide-up" style="animation-delay: 0.4s;">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                    <i class="fas fa-server fa-icon-gradient"></i>
                    <h2 class="text-base sm:text-lg font-bold">
                        <span data-i18n="servers"></span>
                        <span class="text-indigo-400 mx-1">({len(display_configs)})</span>
                    </h2>
                </div>
                <button type="button" id="search-toggle" onclick="toggleSearch()" class="icon-btn w-9 h-9 rounded-xl flex items-center justify-center text-sm">
                    <i class="fas fa-search"></i>
                </button>
            </div>
            
            <div id="search-box" class="hidden mb-4 animate-fade-in">
                <div class="relative">
                    <i class="fas fa-search absolute top-1/2 -translate-y-1/2 right-4 text-slate-400 pointer-events-none"></i>
                    <input type="text" id="config-search" 
                        class="input-field w-full rounded-xl pl-4 pr-10 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-all">
                </div>
            </div>
            
            <div class="space-y-2 max-h-[400px] overflow-y-auto scroll-smooth pr-1" id="configs-list"></div>
        </div>

        <div class="text-center mt-8 space-y-2 animate-fade-in opacity-70" style="animation-delay: 0.6s;">
            <div class="text-xs opacity-70 flex items-center justify-center gap-2">
                <i class="far fa-copyright"></i>
                <span>2026 {brand_name}</span>
            </div>
            <div class="text-xs opacity-60">
                <span data-i18n="subsidiary"></span>
                <a href="{company_website}" target="_blank" class="font-bold text-indigo-400 hover:text-indigo-300 mx-1 inline-flex items-center gap-1">
                    {parent_brand}
                    <i class="fas fa-external-link-alt text-xs"></i>
                </a>
            </div>
        </div>
    </div>

    <div id="qr-modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-md z-[500] items-center justify-center p-4" onclick="closeQR(event)">
        <div class="glass-card rounded-3xl p-6 max-w-sm w-full animate-scale-in" onclick="event.stopPropagation()">
            <div class="text-center mb-4 flex items-center justify-between">
                <div class="text-sm font-bold" id="qr-title"></div>
                <button type="button" onclick="closeQR()" class="icon-btn w-8 h-8 rounded-lg flex items-center justify-center text-xs">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="bg-white p-4 rounded-2xl flex items-center justify-center shadow-2xl">
                <div id="qr-container"></div>
            </div>
            <button type="button" onclick="closeQR()" class="btn-primary w-full mt-4 py-3 text-white text-sm rounded-xl font-medium flex items-center justify-center gap-2">
                <i class="fas fa-check"></i><span data-i18n="close"></span>
            </button>
        </div>
    </div>

    <div id="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-6 py-3 rounded-full text-sm font-medium shadow-2xl opacity-0 pointer-events-none z-[600] transition-all duration-300 flex items-center gap-2" style="transform: translate(-50%, 20px);">
        <i class="fas fa-check-circle"></i>
        <span id="toast-text">Copied</span>
    </div>

    <script>
        const USER_DATA = {user_json};
        const CONFIGS = {configs_json};
        const SERVER_LANG = "{lang}";
        const BRAND_NAME = "{brand_name}";
        
        const TRANSLATIONS = {{
            en: {{
                dir: "ltr",
                subtitle: "Your subscription details",
                username: "Username",
                volume: "Volume",
                unlimited: "Unlimited",
                days_remaining: "Time left",
                days: "days",
                hours: "hours",
                minutes: "minutes",
                time_remaining: "Time left",
                first_use: "First use",
                sub_link: "Your subscription link:",
                copy: "Copy",
                copied: "Copied!",
                add_hint: "Add this link to Hiddify, v2rayNG, or Streisand app for automatic updates.",
                servers: "Servers",
                close: "Close",
                active: "Active",
                blocked: "Blocked",
                inactive: "Expired",
                ready: "Ready",
                not_used: "Not used yet",
                powered_by: "Powered by " + BRAND_NAME,
                subsidiary: "A subsidiary of",
                search: "Search servers..."
            }},
            fa: {{
                dir: "rtl",
                subtitle: "اطلاعات اشتراک شما",
                username: "نام کاربری",
                volume: "حجم",
                unlimited: "نامحدود",
                days_remaining: "زمان باقی‌مانده",
                days: "روز",
                hours: "ساعت",
                minutes: "دقیقه",
                time_remaining: "زمان باقی‌مانده",
                first_use: "اولین استفاده",
                sub_link: "لینک اشتراک شما:",
                copy: "کپی",
                copied: "کپی شد!",
                add_hint: "این لینک را در برنامه Hiddify، v2rayNG یا Streisand اضافه کنید.",
                servers: "سرورها",
                close: "بستن",
                active: "فعال",
                blocked: "مسدود",
                inactive: "منقضی",
                ready: "آماده",
                not_used: "هنوز استفاده نشده",
                powered_by: "قدرت گرفته از " + BRAND_NAME,
                subsidiary: "زیرمجموعه‌ی",
                search: "جستجو در سرورها..."
            }},
            ru: {{
                dir: "ltr",
                subtitle: "Информация о вашей подписке",
                username: "Имя пользователя",
                volume: "Объём",
                unlimited: "Безлимитный",
                days_remaining: "Осталось",
                days: "дней",
                hours: "часов",
                minutes: "минут",
                time_remaining: "Осталось времени",
                first_use: "Первое использование",
                sub_link: "Ваша ссылка подписки:",
                copy: "Копировать",
                copied: "Скопировано!",
                add_hint: "Добавьте эту ссылку в приложение Hiddify, v2rayNG или Streisand.",
                servers: "Серверы",
                close: "Закрыть",
                active: "Активен",
                blocked: "Заблокирован",
                inactive: "Истёк",
                ready: "Готов",
                not_used: "Ещё не использовалось",
                powered_by: "На платформе " + BRAND_NAME,
                subsidiary: "Дочерняя компания",
                search: "Поиск серверов..."
            }}
        }};
        
        const LANG_META = {{
            en: {{ name: "EN" }},
            fa: {{ name: "FA" }},
            ru: {{ name: "RU" }}
        }};

        function getCurrentLang() {{
            const saved = localStorage.getItem('nettap_lang');
            if (saved && TRANSLATIONS[saved]) return saved;
            return SERVER_LANG;
        }}
        
        function setLang(lang) {{
            if (!TRANSLATIONS[lang]) return;
            localStorage.setItem('nettap_lang', lang);
            applyLang(lang);
            const menu = document.getElementById('lang-menu');
            menu.classList.add('hidden');
        }}
        
        function applyLang(lang) {{
            const t = TRANSLATIONS[lang] || TRANSLATIONS.en;
            document.documentElement.setAttribute('lang', lang);
            document.documentElement.setAttribute('dir', t.dir);
            document.body.setAttribute('dir', t.dir);
            
            document.querySelectorAll('[data-i18n]').forEach(el => {{
                const key = el.getAttribute('data-i18n');
                if (t[key] !== undefined) el.textContent = t[key];
            }});
            
            const meta = LANG_META[lang];
            document.getElementById('current-lang-name').textContent = meta.name;
            
            document.querySelectorAll('.check-icon').forEach(icon => icon.classList.add('hidden'));
            document.querySelectorAll('.lang-menu-item').forEach(item => item.classList.remove('active'));
            const activeItem = document.querySelector(`[data-lang="${{lang}}"]`);
            if (activeItem) {{
                activeItem.classList.add('active');
                const check = activeItem.querySelector('.check-icon');
                if (check) check.classList.remove('hidden');
            }}
            
            const search = document.getElementById('config-search');
            if (search) search.placeholder = t.search;
            
            updateStatusBadge(t);
            updateFirstUse(t, lang);
            updateRemainingTimeDisplay(t);
            renderConfigs();
        }}
        
        function updateStatusBadge(t) {{
            const badge = document.getElementById('status-badge');
            if (USER_DATA.is_blocked) {{
                badge.className = 'inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30';
                badge.innerHTML = `<span class="status-dot pulse" style="background: #f87171;"></span>${{t.blocked}} <i class="fas fa-ban"></i>`;
            }} else if (USER_DATA.is_active) {{
                badge.className = 'inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
                badge.innerHTML = `<span class="status-dot pulse" style="background: #34d399;"></span>${{t.active}} <i class="fas fa-check-circle"></i>`;
            }} else {{
                badge.className = 'inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30';
                badge.innerHTML = `<span class="status-dot" style="background: #f87171;"></span>${{t.inactive}} <i class="fas fa-times-circle"></i>`;
            }}
        }}
        
        function updateFirstUse(t, lang) {{
            const el = document.getElementById('first-use-text');
            if (USER_DATA.first_use) {{
                try {{
                    const d = new Date(USER_DATA.first_use);
                    if (lang === 'fa') {{
                        const formatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {{
                            year: 'numeric', month: 'long', day: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                        }});
                        el.textContent = formatter.format(d);
                    }} else {{
                        const locale = lang === 'ru' ? 'ru-RU' : 'en-US';
                        el.textContent = d.toLocaleString(locale, {{ 
                            year: 'numeric', month: 'short', day: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                        }});
                    }}
                }} catch {{ el.textContent = USER_DATA.first_use; }}
            }} else {{
                el.textContent = t.not_used;
            }}
        }}
        
        function updateRemainingTimeDisplay(t) {{
            const daysVal = document.getElementById('days-display-val');
            const daysUnit = document.getElementById('days-unit-val');
            if (!daysVal || !daysUnit) return;
            
            if (!USER_DATA.expire_date) {{
                daysVal.textContent = "—";
                daysUnit.textContent = t.ready;
                return;
            }}
            
            const expire = new Date(USER_DATA.expire_date);
            const now = new Date();
            const diffMs = expire - now;
            
            if (diffMs <= 0) {{
                daysVal.textContent = "✗";
                daysUnit.textContent = t.inactive;
                return;
            }}
            
            const totalMinutes = Math.floor(diffMs / 60000);
            
            if (totalMinutes >= 1440) {{
                daysVal.textContent = Math.floor(totalMinutes / 1440);
                daysUnit.textContent = t.days;
            }} else if (totalMinutes >= 60) {{
                daysVal.textContent = Math.floor(totalMinutes / 60);
                daysUnit.textContent = t.hours;
            }} else {{
                daysVal.textContent = totalMinutes;
                daysUnit.textContent = t.minutes;
            }}
        }}
        
        function getCurrentTheme() {{
            const saved = localStorage.getItem('nettap_theme');
            if (saved) return saved;
            return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
        }}
        
        function applyTheme(theme) {{
            const body = document.body;
            const icon = document.getElementById('theme-icon');
            const meta = document.getElementById('meta-theme');
            
            if (theme === 'light') {{
                body.classList.add('light-mode');
                icon.className = 'fas fa-sun';
                if (meta) meta.setAttribute('content', '#f1f5f9');
            }} else {{
                body.classList.remove('light-mode');
                icon.className = 'fas fa-moon';
                if (meta) meta.setAttribute('content', '#0f172a');
            }}
            localStorage.setItem('nettap_theme', theme);
        }}
        
        function toggleTheme() {{
            const current = document.body.classList.contains('light-mode') ? 'light' : 'dark';
            applyTheme(current === 'dark' ? 'light' : 'dark');
        }}
        
        function animateProgress() {{
            const circle = document.getElementById('progress-circle');
            if (!circle || !USER_DATA.expire_date) return;
            
            const expire = new Date(USER_DATA.expire_date);
            const now = new Date();
            const diffMs = expire - now;
            if (diffMs <= 0) {{
                circle.style.strokeDashoffset = "100.53";
                circle.setAttribute('stroke', '#ef4444');
                return;
            }}
            
            const total_minutes = USER_DATA.duration_minutes || 43200;
            const minutes_remaining = Math.floor(diffMs / 60000);
            const percent = Math.min(100, Math.max(0, (minutes_remaining / total_minutes) * 100));
            
            const circumference = 2 * Math.PI * 16;
            const offset = circumference - (percent / 100) * circumference;
            
            circle.style.strokeDashoffset = offset;
            if (percent < 30) circle.setAttribute('stroke', '#ef4444');
            else if (percent < 60) circle.setAttribute('stroke', '#f59e0b');
            else circle.setAttribute('stroke', '#10b981');
        }}
        
        function renderConfigs(filter = '') {{
            const container = document.getElementById('configs-list');
            
            const filtered = CONFIGS.filter(c => {{
                if (!filter) return true;
                const f = filter.toLowerCase();
                return (c.name || '').toLowerCase().includes(f) ||
                       (c.code || '').toLowerCase().includes(f);
            }});
            
            if (filtered.length === 0) {{
                container.innerHTML = `<div class="text-center py-8 opacity-50 text-sm"><i class="fas fa-search-minus text-2xl mb-2"></i><br>No results</div>`;
                return;
            }}
            
            container.innerHTML = filtered.map((cfg, i) => {{
                let pingClass = 'ping-none';
                let pingText = '—';
                if (cfg.ping > 0) {{
                    pingText = cfg.ping + 'ms';
                    if (cfg.ping < 200) pingClass = 'ping-good';
                    else if (cfg.ping < 500) pingClass = 'ping-medium';
                    else pingClass = 'ping-slow';
                }}
                
                const safeUrl = cfg.url.replace(/`/g, '\\\\`').replace(/\\$/g, '\\\\$');
                const safeName = (cfg.name || '').replace(/`/g, '\\\\`');
                
                return `
                    <div class="config-item rounded-2xl p-3 sm:p-4 flex items-center justify-between gap-3 animate-slide-up" style="animation-delay: ${{i * 0.05}}s;">
                        <div class="flex-1 min-w-0 flex items-center gap-3">
                            <div class="config-flag">${{cfg.flag}}</div>
                            <div class="flex-1 min-w-0">
                                <div class="text-sm font-bold truncate">${{cfg.name}}</div>
                                <div class="text-xs opacity-60 flex items-center gap-1.5 mt-0.5">
                                    <i class="fas fa-flag text-xs"></i>
                                    <span>${{cfg.code}}</span>
                                    <span class="mx-1">•</span>
                                    <i class="fas fa-signal text-xs"></i>
                                    <span>${{pingText}}</span>
                                    <span class="ping-dot ${{pingClass}}"></span>
                                </div>
                            </div>
                        </div>
                        <div class="flex gap-1.5 shrink-0">
                            <button type="button" onclick="showQR(\\`${{safeUrl}}\\`, \\`${{safeName}}\\`)" 
                                class="icon-btn w-9 h-9 rounded-xl flex items-center justify-center text-sm" title="QR">
                                <i class="fas fa-qrcode"></i>
                            </button>
                            <button type="button" onclick="copyCfg(this, \\`${{safeUrl}}\\`)" 
                                class="btn-primary w-9 h-9 rounded-xl flex items-center justify-center text-sm text-white" title="Copy">
                                <i class="far fa-copy"></i>
                            </button>
                        </div>
                    </div>
                `;
            }}).join('');
        }}
        
        function toggleSearch() {{
            const box = document.getElementById('search-box');
            const btn = document.getElementById('search-toggle');
            if (box.classList.contains('hidden')) {{
                box.classList.remove('hidden');
                setTimeout(() => document.getElementById('config-search').focus(), 100);
                btn.style.background = 'rgba(99, 102, 241, 0.2)';
            }} else {{
                box.classList.add('hidden');
                document.getElementById('config-search').value = '';
                renderConfigs();
                btn.style.background = '';
            }}
        }}
        
        function copyCfg(btn, text) {{
            copyToClipboard(text).then(() => {{
                showToast();
                const orig = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i>';
                btn.style.background = 'linear-gradient(135deg, #10b981, #14b8a6)';
                setTimeout(() => {{
                    btn.innerHTML = orig;
                    btn.style.background = '';
                }}, 1500);
            }}).catch(() => {{
                fallbackCopy(text);
                showToast();
            }});
        }}
        
        function copySubLink() {{
            const text = document.getElementById('sub-link').value;
            copyToClipboard(text).then(showToast);
        }}
        
        async function copyToClipboard(text) {{
            try {{
                if (navigator.clipboard && window.isSecureContext) {{
                    await navigator.clipboard.writeText(text);
                    return;
                }}
            }} catch {{}}
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            try {{ document.execCommand('copy'); }} catch {{}}
            document.body.removeChild(ta);
        }}
        
        function showToast(msg) {{
            const toast = document.getElementById('toast');
            const text = document.getElementById('toast-text');
            const t = TRANSLATIONS[getCurrentLang()];
            text.textContent = msg || t.copied;
            toast.style.opacity = '1';
            toast.style.transform = 'translate(-50%, 0)';
            setTimeout(() => {{
                toast.style.opacity = '0';
                toast.style.transform = 'translate(-50%, 20px)';
            }}, 2200);
        }}
        
        function showQR(text, title) {{
            const modal = document.getElementById('qr-modal');
            const container = document.getElementById('qr-container');
            const titleEl = document.getElementById('qr-title');
            container.innerHTML = '';
            titleEl.textContent = title;
            new QRCode(container, {{
                text: text, width: 240, height: 240,
                correctLevel: QRCode.CorrectLevel.M
            }});
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }}
        
        function closeQR(event) {{
            if (event && event.target.id !== 'qr-modal') return;
            const modal = document.getElementById('qr-modal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }}
        
        document.addEventListener('DOMContentLoaded', () => {{
            document.getElementById('theme-toggle').addEventListener('click', (e) => {{
                e.preventDefault();
                e.stopPropagation();
                toggleTheme();
            }});
            
            const langBtn = document.getElementById('lang-btn');
            const langMenu = document.getElementById('lang-menu');
            
            langBtn.addEventListener('click', (e) => {{
                e.preventDefault();
                e.stopPropagation();
                langMenu.classList.toggle('hidden');
            }});
            
            document.addEventListener('click', (e) => {{
                if (!langMenu.contains(e.target) && !langBtn.contains(e.target)) {{
                    langMenu.classList.add('hidden');
                }}
            }});
            
            const search = document.getElementById('config-search');
            if (search) {{
                search.addEventListener('input', (e) => renderConfigs(e.target.value));
            }}
            
            applyTheme(getCurrentTheme());
            applyLang(getCurrentLang());
            
            setTimeout(animateProgress, 500);
        }});
    </script>
</body>
</html>'''

@router.get("/{token}")
def get_subscription(
    token: str, 
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(UserSubscription).filter(UserSubscription.token == token).first()
    if not user:
        return Response(content="Not Found", status_code=404)
    
    brand_name = get_setting(db, "brand_name", "NETtap")
    sub_url_prefix = get_setting(db, "sub_url_prefix", "https://vpn.tahasite.ir")
        
    if user.is_blocked:
        expired_msg = f"⛔ {brand_name} • Blocked"
        configs = [{
            "url": f"vless://11111111-1111-1111-1111-111111111111@1.1.1.1:443?encryption=none&security=tls&type=tcp&sni=blocked.local#{quote(expired_msg)}",
            "name": expired_msg,
            "flag": "⛔",
            "code": "XX",
            "ping": -1,
            "is_info": True
        }]
        is_expired = True
        zone_needs_rebuild = False
    else:
        if not is_browser_request(request):
            is_expired = check_and_activate_user(user, db)
        else:
            is_expired = False
            if user.expire_date and user.expire_date < datetime.utcnow():
                is_expired = True
        configs, zone_needs_rebuild = build_configs_list(db, user, expired=is_expired)
        
    if zone_needs_rebuild:
        background_tasks.add_task(rebuild_zone_file, db)
        
    upload = 0
    download = 0
    total = 0
    expire_timestamp = int(user.expire_date.timestamp()) if user.expire_date else 0
    
    common_headers = {
        "subscription-userinfo": f"upload={upload}; download={download}; total={total}; expire={expire_timestamp}",
        "profile-update-interval": "12",
        "profile-title": f"base64:{base64.b64encode(brand_name.encode()).decode()}",
        "profile-web-page-url": f"{sub_url_prefix}/sub/{token}",
        "support-url": f"{sub_url_prefix}/sub/{token}",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    
    if is_browser_request(request):
        sub_url = f"{sub_url_prefix}/sub/{token}"
        lang = detect_lang_from_ip(request)
        html = render_html_page(user, configs, sub_url, lang, db)
        return HTMLResponse(content=html, headers=common_headers)
    
    format_type = request.query_params.get("format", "").lower()
    config_urls = [c["url"] for c in configs]
    final_output = "\r\n".join(config_urls)
    
    if format_type == "raw" or format_type == "plain":
        headers = {
            **common_headers,
            "Content-Type": "text/plain; charset=utf-8"
        }
        return Response(content=final_output, headers=headers)
    
    encoded_output = base64.b64encode(final_output.encode('utf-8')).decode('utf-8')
    
    user_agent = request.headers.get("user-agent", "").lower()
    content_type = "text/plain; charset=utf-8"
    if "clash" in user_agent or "stash" in user_agent:
        content_type = "application/x-yaml; charset=utf-8"
        
    headers = {
        **common_headers,
        "Content-Type": content_type,
        "Content-Disposition": f'attachment; filename="{brand_name}.txt"'
    }
    return Response(content=encoded_output, headers=headers)