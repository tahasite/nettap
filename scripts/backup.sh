#!/bin/bash

INSTALL_DIR="/opt/nettap"
BACKUP_DIR="/root/nettap-backups"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nettap-backup-$TIMESTAMP.tar.gz"

echo -e "${CYAN}Creating NETtap backup...${NC}"

tar -czf "$BACKUP_FILE" \
    "$INSTALL_DIR/data/" \
    "$INSTALL_DIR/backend/.env" \
    "$INSTALL_DIR/telegram-bot/.env" \
    2>/dev/null

SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')

echo -e "${GREEN}✅ Backup created: $BACKUP_FILE ($SIZE)${NC}"

KEEP=5
cd "$BACKUP_DIR"
ls -t nettap-backup-*.tar.gz 2>/dev/null | tail -n +$((KEEP+1)) | xargs rm -f 2>/dev/null

echo -e "${CYAN}Keeping last $KEEP backups${NC}"

ls -la "$BACKUP_DIR"/nettap-backup-*.tar.gz 2>/dev/null