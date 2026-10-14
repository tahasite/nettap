#!/bin/bash

set -e

GITHUB_REPO="tahasite/nettap"
GITHUB_BRANCH="main"
INSTALL_DIR="/opt/nettap"
DATA_DIR="$INSTALL_DIR/data"
LOGS_DIR="$INSTALL_DIR/logs"
BACKEND_PORT=8734
BOT_PORT=8735

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_step() { echo -e "\n${MAGENTA}${BOLD}▶ $1${NC}\n"; }

show_banner() {
    clear
    echo -e "${MAGENTA}${BOLD}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║                                                   ║"
    echo "║       🛡️   NETtap VPN Panel Installer             ║"
    echo "║                                                   ║"
    echo "║       Version: 1.0.0                              ║"
    echo "║       Author:  TahaSite                           ║"
    echo "║       GitHub:  github.com/tahasite/nettap         ║"
    echo "║                                                   ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        echo -e "${YELLOW}Please run: ${WHITE}sudo bash install.sh${NC}"
        exit 1
    fi
}

check_os() {
    log_step "Checking System Requirements"
    
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot detect OS. This script supports Ubuntu/Debian only."
        exit 1
    fi
    
    source /etc/os-release
    OS_ID=$ID
    OS_VERSION=$VERSION_ID
    
    log_success "Detected: $PRETTY_NAME"
    
    if [[ "$OS_ID" != "ubuntu" && "$OS_ID" != "debian" ]]; then
        log_error "Only Ubuntu and Debian are supported"
        exit 1
    fi
    
    log_success "Running as root"
    
    if ! ping -c 1 -W 3 8.8.8.8 &>/dev/null; then
        log_error "No internet connection detected"
        exit 1
    fi
    log_success "Internet connection OK"
    
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "NETtap seems to be already installed at $INSTALL_DIR"
        read -p "Do you want to reinstall? This will DELETE all existing data! (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
        log_warning "Stopping existing services..."
        systemctl stop nettap-backend nettap-bot coredns 2>/dev/null || true
        systemctl disable nettap-backend nettap-bot 2>/dev/null || true
        rm -rf "$INSTALL_DIR"
        log_success "Old installation removed"
    fi
}

install_dependencies() {
    log_step "Installing System Dependencies"
    
    log_info "Updating package list..."
    DEBIAN_FRONTEND=noninteractive apt-get update -qq
    
    log_info "Installing required packages..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
        curl \
        wget \
        git \
        python3 \
        python3-pip \
        python3-venv \
        nginx \
        certbot \
        python3-certbot-nginx \
        openssl \
        ufw \
        tar \
        gzip \
        dnsutils \
        net-tools >/dev/null 2>&1
    
    log_success "System dependencies installed"
    
    if ! command -v python3 &>/dev/null; then
        log_error "Python 3 installation failed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_success "Python $PYTHON_VERSION installed"
}

install_coredns() {
    log_step "Installing CoreDNS"
    
    if command -v coredns &>/dev/null; then
        COREDNS_VERSION=$(coredns --version | head -n1 | awk '{print $2}')
        log_success "CoreDNS already installed: $COREDNS_VERSION"
        return
    fi
    
    log_info "Downloading CoreDNS v1.11.3..."
    cd /tmp
    curl -sSL -o coredns.tgz "https://github.com/coredns/coredns/releases/download/v1.11.3/coredns_1.11.3_linux_amd64.tgz"
    tar -xzf coredns.tgz
    mv coredns /usr/local/bin/
    chmod +x /usr/local/bin/coredns
    rm -f coredns.tgz
    
    log_success "CoreDNS installed successfully"
}

download_nettap() {
    log_step "Downloading NETtap"
    
    mkdir -p "$INSTALL_DIR"
    cd /tmp
    
    log_info "Cloning from GitHub..."
    if ! git clone --depth 1 --branch "$GITHUB_BRANCH" "https://github.com/$GITHUB_REPO.git" nettap-src >/dev/null 2>&1; then
        log_error "Failed to download from GitHub"
        exit 1
    fi
    
    cp -r nettap-src/backend "$INSTALL_DIR/"
    cp -r nettap-src/frontend "$INSTALL_DIR/"
    cp -r nettap-src/telegram-bot "$INSTALL_DIR/"
    cp -r nettap-src/templates "$INSTALL_DIR/"
    cp -r nettap-src/scripts "$INSTALL_DIR/"
    
    rm -rf nettap-src
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    
    log_success "NETtap source downloaded to $INSTALL_DIR"
}

setup_python_backend() {
    log_step "Setting Up Python Backend"
    
    cd "$INSTALL_DIR/backend"
    
    log_info "Creating virtual environment..."
    python3 -m venv venv
    
    log_info "Installing Python packages (this may take a few minutes)..."
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    deactivate
    
    log_success "Backend Python environment ready"
}

setup_python_bot() {
    log_step "Setting Up Telegram Bot"
    
    cd "$INSTALL_DIR/telegram-bot"
    
    log_info "Creating virtual environment..."
    python3 -m venv venv
    
    log_info "Installing Python packages..."
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    pip install "python-telegram-bot[webhooks]" --quiet
    deactivate
    
    log_success "Telegram Bot Python environment ready"
}

download_vendors() {
    log_step "Downloading Frontend Vendor Files"
    
    VENDOR_DIR="$INSTALL_DIR/frontend/admin/assets/vendor"
    mkdir -p "$VENDOR_DIR"
    mkdir -p "$VENDOR_DIR/fontawesome/css"
    mkdir -p "$VENDOR_DIR/fontawesome/webfonts"
    
    log_info "Downloading TailwindCSS..."
    curl -sSL -o "$VENDOR_DIR/tailwindcss.js" "https://cdn.tailwindcss.com/3.4.0" || \
        curl -sSL -o "$VENDOR_DIR/tailwindcss.js" "https://unpkg.com/@tailwindcss/browser@4"
    
    log_info "Downloading QRCode.js..."
    curl -sSL -o "$VENDOR_DIR/qrcode.min.js" "https://cdn.jsdelivr.net/gh/davidshimjs/qrcodejs/qrcode.min.js"
    
    log_info "Downloading FontAwesome..."
    cd /tmp
    curl -sSL -o fa.zip "https://use.fontawesome.com/releases/v6.5.1/fontawesome-free-6.5.1-web.zip"
    if [[ -f fa.zip ]]; then
        apt-get install -y -qq unzip >/dev/null 2>&1
        unzip -q fa.zip
        FA_DIR=$(ls -d fontawesome-free-*/ 2>/dev/null | head -n1)
        if [[ -n "$FA_DIR" ]]; then
            cp "$FA_DIR/css/all.min.css" "$VENDOR_DIR/fontawesome/css/"
            cp "$FA_DIR/webfonts/"* "$VENDOR_DIR/fontawesome/webfonts/"
            rm -rf "$FA_DIR" fa.zip
        fi
    fi
    
    log_info "Downloading Vazir Font..."
    FONT_DIR="$INSTALL_DIR/frontend/admin/assets/fonts/Vazir"
    mkdir -p "$FONT_DIR"
    for weight in "" "-Bold" "-Light" "-Medium" "-Thin" "-Black"; do
        curl -sSL -o "$FONT_DIR/Vazir${weight}.woff2" \
            "https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@master/dist/Vazir${weight}.woff2" 2>/dev/null || true
    done
    
    log_success "Frontend vendor files downloaded"
}

configure_wizard() {
    log_step "Configuration Wizard"
    
    echo -e "${CYAN}Please answer the following questions:${NC}\n"
    
    DETECTED_IP=$(curl -sS -4 --max-time 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')
    
    while true; do
        read -p "$(echo -e ${WHITE}🌐 Panel Domain ${CYAN}\(e.g. panel.yourdomain.com\)${WHITE}: ${NC})" PANEL_DOMAIN
        if [[ -n "$PANEL_DOMAIN" && "$PANEL_DOMAIN" =~ ^[a-zA-Z0-9.-]+$ ]]; then
            break
        fi
        log_warning "Invalid domain. Please try again."
    done
    
    while true; do
        read -p "$(echo -e ${WHITE}🌍 DNS Domain for user subdomains ${CYAN}\(e.g. dns.yourdomain.com\)${WHITE}: ${NC})" DNS_DOMAIN
        if [[ -n "$DNS_DOMAIN" && "$DNS_DOMAIN" =~ ^[a-zA-Z0-9.-]+$ ]]; then
            break
        fi
        log_warning "Invalid domain. Please try again."
    done
    
    read -p "$(echo -e ${WHITE}🖥️  Server IP ${CYAN}[$DETECTED_IP]${WHITE}: ${NC})" SERVER_IP
    SERVER_IP=${SERVER_IP:-$DETECTED_IP}
    
    read -p "$(echo -e ${WHITE}🔑 Admin Username ${CYAN}[admin]${WHITE}: ${NC})" ADMIN_USER
    ADMIN_USER=${ADMIN_USER:-admin}
    
    read -p "$(echo -e ${WHITE}🔒 Admin Password ${CYAN}\(leave empty to auto-generate\)${WHITE}: ${NC})" ADMIN_PASS
    if [[ -z "$ADMIN_PASS" ]]; then
        ADMIN_PASS=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-14)
        log_info "Auto-generated password: ${YELLOW}$ADMIN_PASS${NC}"
    fi
    
    echo ""
    read -p "$(echo -e ${WHITE}🔐 Install SSL with Let\'s Encrypt? ${CYAN}[Y/n]${WHITE}: ${NC})" INSTALL_SSL
    INSTALL_SSL=${INSTALL_SSL:-Y}
    
    if [[ "$INSTALL_SSL" =~ ^[Yy]$ ]]; then
        read -p "$(echo -e ${WHITE}📧 Email for SSL ${CYAN}\(required\)${WHITE}: ${NC})" SSL_EMAIL
        while [[ -z "$SSL_EMAIL" ]]; do
            read -p "$(echo -e ${YELLOW}Email is required: ${NC})" SSL_EMAIL
        done
    fi
    
    SECRET_KEY=$(openssl rand -hex 32)
    
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════${NC}"
    echo -e "${WHITE}Configuration Summary:${NC}"
    echo -e "  Panel Domain:  ${YELLOW}$PANEL_DOMAIN${NC}"
    echo -e "  DNS Domain:    ${YELLOW}$DNS_DOMAIN${NC}"
    echo -e "  Server IP:     ${YELLOW}$SERVER_IP${NC}"
    echo -e "  Admin User:    ${YELLOW}$ADMIN_USER${NC}"
    echo -e "  Admin Pass:    ${YELLOW}$ADMIN_PASS${NC}"
    echo -e "  Install SSL:   ${YELLOW}$INSTALL_SSL${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════${NC}\n"
    
    read -p "$(echo -e ${WHITE}Continue with installation? ${CYAN}[Y/n]${WHITE}: ${NC})" CONFIRM
    CONFIRM=${CONFIRM:-Y}
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled by user"
        exit 0
    fi
}

configure_env_files() {
    log_step "Configuring Environment Files"
    
    log_info "Creating backend .env..."
    sed -e "s|{{BACKEND_PORT}}|$BACKEND_PORT|g" \
        -e "s|{{SECRET_KEY}}|$SECRET_KEY|g" \
        -e "s|{{DNS_DOMAIN}}|$DNS_DOMAIN|g" \
        -e "s|{{SERVER_IP}}|$SERVER_IP|g" \
        "$INSTALL_DIR/templates/backend.env.template" > "$INSTALL_DIR/backend/.env"
    
    log_info "Creating bot .env..."
    sed -e "s|{{BACKEND_PORT}}|$BACKEND_PORT|g" \
        -e "s|{{BOT_PORT}}|$BOT_PORT|g" \
        -e "s|{{ADMIN_USER}}|$ADMIN_USER|g" \
        -e "s|{{ADMIN_PASS}}|$ADMIN_PASS|g" \
        "$INSTALL_DIR/templates/bot.env.template" > "$INSTALL_DIR/telegram-bot/.env"
    
    log_success "Environment files created"
}

configure_coredns() {
    log_step "Configuring CoreDNS"
    
    SERIAL=$(date +%s)
    
    sed -e "s|{{DNS_DOMAIN}}|$DNS_DOMAIN|g" \
        "$INSTALL_DIR/templates/Corefile.template" > "$DATA_DIR/Corefile"
    
    sed -e "s|{{DNS_DOMAIN}}|$DNS_DOMAIN|g" \
        -e "s|{{SERVER_IP}}|$SERVER_IP|g" \
        -e "s|{{SERIAL}}|$SERIAL|g" \
        "$INSTALL_DIR/templates/zone.db.template" > "$DATA_DIR/zone.db"
    
    log_info "Freeing port 53..."
    systemctl disable --now systemd-resolved 2>/dev/null || true
    rm -f /etc/resolv.conf
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf
    chattr +i /etc/resolv.conf 2>/dev/null || true
    
    sed -e "s|/opt/nettap/data/Corefile|$DATA_DIR/Corefile|g" \
        "$INSTALL_DIR/templates/coredns.service.template" > /etc/systemd/system/coredns.service
    
    log_success "CoreDNS configured"
}

configure_services() {
    log_step "Setting Up Systemd Services"
    
    sed -e "s|{{BACKEND_PORT}}|$BACKEND_PORT|g" \
        "$INSTALL_DIR/templates/nettap-backend.service.template" > /etc/systemd/system/nettap-backend.service
    
    cp "$INSTALL_DIR/templates/nettap-bot.service.template" /etc/systemd/system/nettap-bot.service
    
    systemctl daemon-reload
    
    log_success "Systemd services configured"
}

configure_nginx() {
    log_step "Configuring Nginx"
    
    if [[ "$INSTALL_SSL" =~ ^[Yy]$ ]]; then
        SSL_CERT_PATH="/etc/letsencrypt/live/$PANEL_DOMAIN/fullchain.pem"
        SSL_KEY_PATH="/etc/letsencrypt/live/$PANEL_DOMAIN/privkey.pem"
    else
        mkdir -p /etc/ssl/nettap
        openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
            -keyout /etc/ssl/nettap/key.pem \
            -out /etc/ssl/nettap/cert.pem \
            -subj "/CN=$PANEL_DOMAIN" 2>/dev/null
        SSL_CERT_PATH="/etc/ssl/nettap/cert.pem"
        SSL_KEY_PATH="/etc/ssl/nettap/key.pem"
    fi
    
    sed -e "s|{{PANEL_DOMAIN}}|$PANEL_DOMAIN|g" \
        -e "s|{{BACKEND_PORT}}|$BACKEND_PORT|g" \
        -e "s|{{BOT_PORT}}|$BOT_PORT|g" \
        -e "s|{{SSL_CERT_PATH}}|$SSL_CERT_PATH|g" \
        -e "s|{{SSL_KEY_PATH}}|$SSL_KEY_PATH|g" \
        "$INSTALL_DIR/templates/nginx.conf.template" > /etc/nginx/sites-available/nettap
    
    ln -sf /etc/nginx/sites-available/nettap /etc/nginx/sites-enabled/nettap
    rm -f /etc/nginx/sites-enabled/default
    
    nginx -t >/dev/null 2>&1
    
    if [[ "$INSTALL_SSL" =~ ^[Yy]$ ]]; then
        log_info "Obtaining SSL certificate..."
        systemctl restart nginx
        
        certbot certonly --nginx --non-interactive --agree-tos \
            --email "$SSL_EMAIL" -d "$PANEL_DOMAIN" >/dev/null 2>&1 || {
            log_warning "SSL installation failed. Using self-signed certificate instead."
            mkdir -p /etc/ssl/nettap
            openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
                -keyout /etc/ssl/nettap/key.pem \
                -out /etc/ssl/nettap/cert.pem \
                -subj "/CN=$PANEL_DOMAIN" 2>/dev/null
            sed -i "s|$SSL_CERT_PATH|/etc/ssl/nettap/cert.pem|g" /etc/nginx/sites-available/nettap
            sed -i "s|$SSL_KEY_PATH|/etc/ssl/nettap/key.pem|g" /etc/nginx/sites-available/nettap
        }
    fi
    
    systemctl restart nginx
    log_success "Nginx configured"
}

configure_firewall() {
    log_step "Configuring Firewall"
    
    if command -v ufw &>/dev/null; then
        ufw --force reset >/dev/null 2>&1
        ufw default deny incoming >/dev/null 2>&1
        ufw default allow outgoing >/dev/null 2>&1
        ufw allow 22/tcp >/dev/null 2>&1
        ufw allow 80/tcp >/dev/null 2>&1
        ufw allow 443/tcp >/dev/null 2>&1
        ufw allow 53/udp >/dev/null 2>&1
        ufw allow 53/tcp >/dev/null 2>&1
        ufw --force enable >/dev/null 2>&1
        log_success "Firewall configured"
    else
        log_warning "UFW not available, skipping firewall configuration"
    fi
}

create_admin_user() {
    log_step "Creating Admin User"
    
    cd "$INSTALL_DIR/backend"
    source venv/bin/activate
    
    python3 << EOF
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal, engine, Base
from app.models import Admin
from app.utils.security import get_password_hash

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    existing = db.query(Admin).filter(Admin.username == "$ADMIN_USER").first()
    if existing:
        existing.password_hash = get_password_hash("$ADMIN_PASS")
        print("Admin password updated")
    else:
        admin = Admin(username="$ADMIN_USER", password_hash=get_password_hash("$ADMIN_PASS"))
        db.add(admin)
        print("Admin created")
    db.commit()
finally:
    db.close()
EOF
    
    deactivate
    log_success "Admin user ready"
}

install_cli() {
    log_step "Installing CLI Command"
    
    cp "$INSTALL_DIR/scripts/nettap-cli.sh" /usr/local/bin/nettap
    chmod +x /usr/local/bin/nettap
    
    log_success "CLI installed: ${YELLOW}nettap${NC}"
}

start_services() {
    log_step "Starting Services"
    
    log_info "Enabling and starting backend..."
    systemctl enable nettap-backend >/dev/null 2>&1
    systemctl start nettap-backend
    sleep 3
    
    log_info "Enabling and starting CoreDNS..."
    systemctl enable coredns >/dev/null 2>&1
    systemctl start coredns
    sleep 1
    
    log_info "Enabling Telegram bot (will not start until configured)..."
    systemctl enable nettap-bot >/dev/null 2>&1
    
    systemctl restart nginx
    
    log_success "Services started"
    
    sleep 2
    if systemctl is-active --quiet nettap-backend; then
        log_success "Backend is running"
    else
        log_error "Backend failed to start. Check: journalctl -u nettap-backend"
    fi
    
    if systemctl is-active --quiet coredns; then
        log_success "CoreDNS is running"
    else
        log_warning "CoreDNS failed to start"
    fi
}

show_completion() {
    PROTOCOL="https"
    [[ "$INSTALL_SSL" != "Y" && "$INSTALL_SSL" != "y" ]] && PROTOCOL="https"
    
    clear
    echo -e "${GREEN}${BOLD}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║                                                   ║"
    echo "║        🎉 Installation Complete!                  ║"
    echo "║                                                   ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    echo -e "${CYAN}${BOLD}📋 Access Information:${NC}\n"
    echo -e "  🌐 ${WHITE}Panel URL:${NC}    ${YELLOW}${PROTOCOL}://${PANEL_DOMAIN}/admin/${NC}"
    echo -e "  🔑 ${WHITE}Username:${NC}     ${YELLOW}${ADMIN_USER}${NC}"
    echo -e "  🔒 ${WHITE}Password:${NC}     ${YELLOW}${ADMIN_PASS}${NC}"
    echo ""
    
    echo -e "${CYAN}${BOLD}🎮 CLI Commands:${NC}\n"
    echo -e "  ${WHITE}nettap${NC}              ${CYAN}# Open control menu${NC}"
    echo -e "  ${WHITE}nettap status${NC}       ${CYAN}# Check services${NC}"
    echo -e "  ${WHITE}nettap restart${NC}      ${CYAN}# Restart services${NC}"
    echo -e "  ${WHITE}nettap logs${NC}         ${CYAN}# View logs${NC}"
    echo -e "  ${WHITE}nettap update${NC}       ${CYAN}# Update to latest${NC}"
    echo ""
    
    echo -e "${CYAN}${BOLD}📝 Next Steps:${NC}\n"
    echo -e "  1. Login to the panel"
    echo -e "  2. Go to ${YELLOW}Settings${NC} and configure your preferences"
    echo -e "  3. Add seller subscriptions in ${YELLOW}Seller Subs${NC}"
    echo -e "  4. (Optional) Configure Telegram Bot in ${YELLOW}Settings → Telegram${NC}"
    echo ""
    
    echo -e "${CYAN}${BOLD}⚠️  IMPORTANT:${NC}\n"
    echo -e "  ${YELLOW}Save your admin password now!${NC}"
    echo -e "  You can reset it later with: ${WHITE}nettap admin reset${NC}"
    echo ""
    
    echo -e "${CYAN}${BOLD}💬 Support:${NC}\n"
    echo -e "  ${WHITE}Telegram:${NC}  https://t.me/tahasite_chanel"
    echo -e "  ${WHITE}GitHub:${NC}    https://github.com/tahasite/nettap"
    echo ""
    
    echo -e "${MAGENTA}${BOLD}═══════════════════════════════════════════════════${NC}\n"
}

main() {
    show_banner
    check_root
    check_os
    install_dependencies
    install_coredns
    download_nettap
    setup_python_backend
    setup_python_bot
    download_vendors
    configure_wizard
    configure_env_files
    configure_coredns
    configure_services
    configure_nginx
    configure_firewall
    create_admin_user
    install_cli
    start_services
    show_completion
}

main "$@"