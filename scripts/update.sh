#!/bin/bash

set -e

INSTALL_DIR="/opt/nettap"
GITHUB_REPO="tahasite/nettap"
GITHUB_BRANCH="main"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🔄 Updating NETtap...${NC}\n"

echo -e "${YELLOW}Creating backup before update...${NC}"
BACKUP_FILE="/root/nettap-pre-update-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" \
    "$INSTALL_DIR/data/" \
    "$INSTALL_DIR/backend/.env" \
    "$INSTALL_DIR/telegram-bot/.env" \
    2>/dev/null || true
echo -e "${GREEN}✓ Backup: $BACKUP_FILE${NC}"

echo -e "${CYAN}Downloading latest version...${NC}"
cd /tmp
rm -rf nettap-update
git clone --depth 1 --branch "$GITHUB_BRANCH" "https://github.com/$GITHUB_REPO.git" nettap-update >/dev/null 2>&1

echo -e "${CYAN}Stopping services...${NC}"
systemctl stop nettap-bot 2>/dev/null || true
systemctl stop nettap-backend 2>/dev/null || true

echo -e "${CYAN}Updating files...${NC}"
cp -r nettap-update/backend/app/* "$INSTALL_DIR/backend/app/"
cp -r nettap-update/frontend/* "$INSTALL_DIR/frontend/"
cp -r nettap-update/telegram-bot/*.py "$INSTALL_DIR/telegram-bot/"
cp -r nettap-update/telegram-bot/handlers/* "$INSTALL_DIR/telegram-bot/handlers/"
cp -r nettap-update/telegram-bot/services/* "$INSTALL_DIR/telegram-bot/services/"
cp -r nettap-update/scripts/* "$INSTALL_DIR/scripts/"
cp -r nettap-update/templates/* "$INSTALL_DIR/templates/"

cp nettap-update/backend/requirements.txt "$INSTALL_DIR/backend/"
cp nettap-update/telegram-bot/requirements.txt "$INSTALL_DIR/telegram-bot/"

chmod +x "$INSTALL_DIR/scripts/"*.sh
cp "$INSTALL_DIR/scripts/nettap-cli.sh" /usr/local/bin/nettap
chmod +x /usr/local/bin/nettap

rm -rf nettap-update

echo -e "${CYAN}Updating Python packages...${NC}"
cd "$INSTALL_DIR/backend"
source venv/bin/activate
pip install -r requirements.txt --quiet 2>/dev/null
deactivate

cd "$INSTALL_DIR/telegram-bot"
source venv/bin/activate
pip install -r requirements.txt --quiet 2>/dev/null
deactivate

echo -e "${CYAN}Starting services...${NC}"
systemctl daemon-reload
systemctl start nettap-backend
systemctl start nettap-bot 2>/dev/null || true
systemctl restart nginx

echo -e "\n${GREEN}✅ NETtap updated successfully!${NC}"
echo -e "${YELLOW}Pre-update backup: $BACKUP_FILE${NC}\n"