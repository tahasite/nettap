#!/bin/bash

INSTALL_DIR="/opt/nettap"
BACKUP_DIR="/root/nettap-backups"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}NETtap Restore Tool${NC}\n"

if [[ -n "$1" ]]; then
    BACKUP_FILE="$1"
else
    echo -e "${WHITE}Available backups:${NC}\n"
    ls -la "$BACKUP_DIR"/nettap-backup-*.tar.gz /root/nettap-*.tar.gz 2>/dev/null || echo "No backups found"
    echo ""
    read -p "Enter backup file path: " BACKUP_FILE
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}File not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}This will overwrite current data!${NC}"
read -p "Continue? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Restore cancelled${NC}"
    exit 0
fi

echo -e "${CYAN}Stopping services...${NC}"
systemctl stop nettap-backend nettap-bot 2>/dev/null || true

echo -e "${CYAN}Restoring from backup...${NC}"
tar -xzf "$BACKUP_FILE" -C / 2>/dev/null

echo -e "${CYAN}Starting services...${NC}"
systemctl start nettap-backend
systemctl start nettap-bot 2>/dev/null || true

echo -e "\n${GREEN}✅ Restore complete!${NC}"