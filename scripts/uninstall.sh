#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="/opt/nettap"

echo -e "${RED}╔═══════════════════════════════════════════╗"
echo "║       ⚠️  NETtap Uninstaller              ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}This will permanently remove NETtap and all data!${NC}\n"

read -p "Create a backup before uninstalling? (Y/n): " backup
backup=${backup:-Y}

if [[ "$backup" =~ ^[Yy]$ ]]; then
    BACKUP_FILE="/root/nettap-final-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    echo -e "${CYAN}Creating backup...${NC}"
    tar -czf "$BACKUP_FILE" "$INSTALL_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓ Backup saved: $BACKUP_FILE${NC}\n"
fi

read -p "Type 'REMOVE' to confirm uninstallation: " confirm
if [[ "$confirm" != "REMOVE" ]]; then
    echo -e "${GREEN}Uninstallation cancelled${NC}"
    exit 0
fi

echo -e "\n${CYAN}Stopping services...${NC}"
systemctl stop nettap-bot 2>/dev/null || true
systemctl stop nettap-backend 2>/dev/null || true
systemctl stop coredns 2>/dev/null || true

echo -e "${CYAN}Disabling services...${NC}"
systemctl disable nettap-bot 2>/dev/null || true
systemctl disable nettap-backend 2>/dev/null || true
systemctl disable coredns 2>/dev/null || true

echo -e "${CYAN}Removing service files...${NC}"
rm -f /etc/systemd/system/nettap-backend.service
rm -f /etc/systemd/system/nettap-bot.service
rm -f /etc/systemd/system/coredns.service
systemctl daemon-reload

echo -e "${CYAN}Removing Nginx config...${NC}"
rm -f /etc/nginx/sites-enabled/nettap
rm -f /etc/nginx/sites-available/nettap
systemctl restart nginx 2>/dev/null || true

echo -e "${CYAN}Removing CLI command...${NC}"
rm -f /usr/local/bin/nettap

echo -e "${CYAN}Removing installation directory...${NC}"
rm -rf "$INSTALL_DIR"

echo -e "${CYAN}Removing CoreDNS binary...${NC}"
rm -f /usr/local/bin/coredns

echo -e "${CYAN}Restoring DNS resolver...${NC}"
chattr -i /etc/resolv.conf 2>/dev/null || true
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
systemctl enable --now systemd-resolved 2>/dev/null || true

echo -e "\n${GREEN}╔═══════════════════════════════════════════╗"
echo "║       ✅ NETtap removed successfully       ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

if [[ "$backup" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Your backup is at: $BACKUP_FILE${NC}"
fi

echo -e "${CYAN}To reinstall NETtap:${NC}"
echo -e "  bash <(curl -sSL https://raw.githubusercontent.com/tahasite/nettap/main/scripts/install.sh)\n"