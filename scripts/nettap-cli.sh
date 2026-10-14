#!/bin/bash

INSTALL_DIR="/opt/nettap"
VERSION="1.0.0"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

get_status() {
    if systemctl is-active --quiet "$1" 2>/dev/null; then
        echo -e "${GREEN}● Running${NC}"
    else
        echo -e "${RED}● Stopped${NC}"
    fi
}

show_menu() {
    clear
    echo -e "${MAGENTA}${BOLD}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║       🛡️  NETtap Control Panel            ║"
    echo "║       Version: $VERSION                       ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${CYAN}Service Status:${NC}"
    echo -e "  Backend:  $(get_status nettap-backend)"
    echo -e "  Bot:      $(get_status nettap-bot)"
    echo -e "  CoreDNS:  $(get_status coredns)"
    echo -e "  Nginx:    $(get_status nginx)"
    echo ""
    
    echo -e "${WHITE}Commands:${NC}"
    echo -e "  ${CYAN}1)${NC} Start all services"
    echo -e "  ${CYAN}2)${NC} Stop all services"
    echo -e "  ${CYAN}3)${NC} Restart all services"
    echo -e "  ${CYAN}4)${NC} View logs"
    echo -e "  ${CYAN}5)${NC} Update NETtap"
    echo -e "  ${CYAN}6)${NC} Create backup"
    echo -e "  ${CYAN}7)${NC} Restore backup"
    echo -e "  ${CYAN}8)${NC} Reset admin password"
    echo -e "  ${CYAN}9)${NC} Uninstall"
    echo -e "  ${CYAN}0)${NC} Exit"
    echo ""
    
    read -p "$(echo -e ${WHITE}Enter choice: ${NC})" choice
    
    case $choice in
        1) cmd_start ;;
        2) cmd_stop ;;
        3) cmd_restart ;;
        4) cmd_logs_menu ;;
        5) cmd_update ;;
        6) cmd_backup ;;
        7) cmd_restore ;;
        8) cmd_reset_admin ;;
        9) cmd_uninstall ;;
        0) exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}"; sleep 1; show_menu ;;
    esac
}

cmd_start() {
    echo -e "${CYAN}Starting services...${NC}"
    systemctl start coredns 2>/dev/null
    systemctl start nettap-backend
    systemctl start nettap-bot 2>/dev/null
    systemctl restart nginx
    echo -e "${GREEN}All services started${NC}"
    sleep 2
    show_menu
}

cmd_stop() {
    echo -e "${YELLOW}Stopping services...${NC}"
    systemctl stop nettap-bot 2>/dev/null
    systemctl stop nettap-backend
    echo -e "${GREEN}Services stopped${NC}"
    sleep 2
    show_menu
}

cmd_restart() {
    echo -e "${CYAN}Restarting services...${NC}"
    systemctl restart coredns 2>/dev/null
    systemctl restart nettap-backend
    systemctl restart nettap-bot 2>/dev/null
    systemctl restart nginx
    echo -e "${GREEN}All services restarted${NC}"
    sleep 2
    show_menu
}

cmd_logs_menu() {
    echo ""
    echo -e "${WHITE}Select log:${NC}"
    echo -e "  ${CYAN}1)${NC} Backend"
    echo -e "  ${CYAN}2)${NC} Bot"
    echo -e "  ${CYAN}3)${NC} CoreDNS"
    echo -e "  ${CYAN}4)${NC} Nginx"
    echo -e "  ${CYAN}5)${NC} All (live)"
    echo -e "  ${CYAN}0)${NC} Back"
    echo ""
    read -p "Choice: " log_choice
    
    case $log_choice in
        1) journalctl -u nettap-backend -n 50 --no-pager; read -p "Press Enter..." ;;
        2) journalctl -u nettap-bot -n 50 --no-pager; read -p "Press Enter..." ;;
        3) journalctl -u coredns -n 50 --no-pager; read -p "Press Enter..." ;;
        4) tail -50 /var/log/nginx/nettap_error.log 2>/dev/null; read -p "Press Enter..." ;;
        5) journalctl -u nettap-backend -u nettap-bot -u coredns -f ;;
        0) ;;
    esac
    show_menu
}

cmd_update() {
    echo -e "${CYAN}Updating NETtap...${NC}"
    if [[ -f "$INSTALL_DIR/scripts/update.sh" ]]; then
        bash "$INSTALL_DIR/scripts/update.sh"
    else
        echo -e "${YELLOW}Downloading update script...${NC}"
        bash <(curl -sSL https://raw.githubusercontent.com/tahasite/nettap/main/scripts/update.sh)
    fi
    read -p "Press Enter..."
    show_menu
}

cmd_backup() {
    echo -e "${CYAN}Creating backup...${NC}"
    if [[ -f "$INSTALL_DIR/scripts/backup.sh" ]]; then
        bash "$INSTALL_DIR/scripts/backup.sh"
    else
        BACKUP_FILE="/root/nettap-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        tar -czf "$BACKUP_FILE" \
            "$INSTALL_DIR/data/" \
            "$INSTALL_DIR/backend/.env" \
            "$INSTALL_DIR/telegram-bot/.env" \
            2>/dev/null
        echo -e "${GREEN}Backup saved: $BACKUP_FILE${NC}"
    fi
    read -p "Press Enter..."
    show_menu
}

cmd_restore() {
    echo ""
    echo -e "${WHITE}Available backups:${NC}"
    ls -la /root/nettap-backup-*.tar.gz 2>/dev/null || echo "No backups found"
    echo ""
    read -p "Enter backup file path: " backup_path
    
    if [[ -f "$backup_path" ]]; then
        echo -e "${YELLOW}Stopping services...${NC}"
        systemctl stop nettap-backend nettap-bot 2>/dev/null
        
        echo -e "${CYAN}Restoring...${NC}"
        tar -xzf "$backup_path" -C / 2>/dev/null
        
        echo -e "${GREEN}Restarting services...${NC}"
        systemctl start nettap-backend
        systemctl start nettap-bot 2>/dev/null
        
        echo -e "${GREEN}Restore complete${NC}"
    else
        echo -e "${RED}File not found${NC}"
    fi
    read -p "Press Enter..."
    show_menu
}

cmd_reset_admin() {
    read -p "New admin username [admin]: " new_user
    new_user=${new_user:-admin}
    
    read -p "New admin password (leave empty to auto-generate): " new_pass
    if [[ -z "$new_pass" ]]; then
        new_pass=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-14)
        echo -e "${YELLOW}Generated password: $new_pass${NC}"
    fi
    
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
    admin = db.query(Admin).filter(Admin.username == "$new_user").first()
    if admin:
        admin.password_hash = get_password_hash("$new_pass")
    else:
        db.query(Admin).delete()
        admin = Admin(username="$new_user", password_hash=get_password_hash("$new_pass"))
        db.add(admin)
    db.commit()
    print("Admin updated successfully")
finally:
    db.close()
EOF
    
    deactivate
    
    echo -e "\n${GREEN}Admin credentials updated:${NC}"
    echo -e "  Username: ${YELLOW}$new_user${NC}"
    echo -e "  Password: ${YELLOW}$new_pass${NC}"
    
    read -p "Press Enter..."
    show_menu
}

cmd_uninstall() {
    echo -e "${RED}${BOLD}WARNING: This will remove NETtap completely!${NC}"
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    
    if [[ "$confirm" == "yes" ]]; then
        if [[ -f "$INSTALL_DIR/scripts/uninstall.sh" ]]; then
            bash "$INSTALL_DIR/scripts/uninstall.sh"
        else
            bash <(curl -sSL https://raw.githubusercontent.com/tahasite/nettap/main/scripts/uninstall.sh)
        fi
    else
        echo -e "${GREEN}Uninstall cancelled${NC}"
        sleep 2
        show_menu
    fi
}

cmd_status() {
    echo -e "${CYAN}${BOLD}NETtap Service Status:${NC}\n"
    echo -e "  Backend:   $(get_status nettap-backend)"
    echo -e "  Bot:       $(get_status nettap-bot)"
    echo -e "  CoreDNS:   $(get_status coredns)"
    echo -e "  Nginx:     $(get_status nginx)"
    echo ""
}

case "${1:-}" in
    start)     cmd_start ;;
    stop)      cmd_stop ;;
    restart)   cmd_restart ;;
    status)    cmd_status ;;
    logs)      journalctl -u nettap-backend -u nettap-bot -f ;;
    update)    cmd_update ;;
    backup)    cmd_backup ;;
    uninstall) cmd_uninstall ;;
    admin)
        case "${2:-}" in
            reset) cmd_reset_admin ;;
            *) echo "Usage: nettap admin reset" ;;
        esac
        ;;
    help|--help|-h)
        echo ""
        echo -e "${CYAN}NETtap CLI v$VERSION${NC}"
        echo ""
        echo "Usage: nettap [command]"
        echo ""
        echo "Commands:"
        echo "  (none)        Open interactive menu"
        echo "  start         Start all services"
        echo "  stop          Stop all services"
        echo "  restart       Restart all services"
        echo "  status        Show service status"
        echo "  logs          View live logs"
        echo "  update        Update to latest version"
        echo "  backup        Create data backup"
        echo "  uninstall     Remove NETtap"
        echo "  admin reset   Reset admin password"
        echo "  help          Show this help"
        echo ""
        ;;
    "")
        show_menu
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run 'nettap help' for available commands"
        ;;
esac