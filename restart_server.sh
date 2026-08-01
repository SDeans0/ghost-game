#!/bin/bash
# Script to restart the Ghost Game server with gunicorn and nginx
# Usage: sudo ./restart_server.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Ghost Game Server Restart Script ===${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

# Application directory
APP_DIR="/var/www/ghost-game"  # Update this to your actual deployment path
GUNICORN_SERVICE="gunicorn-ghost-game"  # Name of your systemd service

echo -e "${YELLOW}[1/5] Stopping gunicorn service...${NC}"
if systemctl is-active --quiet "$GUNICORN_SERVICE"; then
    systemctl stop "$GUNICORN_SERVICE"
    echo -e "${GREEN}✓ Gunicorn service stopped${NC}"
else
    echo -e "${YELLOW}⚠ Gunicorn service was not running${NC}"
fi

echo ""
echo -e "${YELLOW}[2/5] Pulling latest code (optional - comment out if not using git)...${NC}"
# Uncomment these lines if you want to pull latest code from git
# cd "$APP_DIR"
# sudo -u www-data git pull origin main
# echo -e "${GREEN}✓ Code updated${NC}"
echo -e "${YELLOW}⚠ Git pull skipped (uncomment in script to enable)${NC}"

echo ""
echo -e "${YELLOW}[3/5] Starting gunicorn service...${NC}"
systemctl start "$GUNICORN_SERVICE"
sleep 2

# Check if service started successfully
if systemctl is-active --quiet "$GUNICORN_SERVICE"; then
    echo -e "${GREEN}✓ Gunicorn service started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start gunicorn service${NC}"
    echo "Service status:"
    systemctl status "$GUNICORN_SERVICE" --no-pager
    exit 1
fi

echo ""
echo -e "${YELLOW}[4/5] Testing nginx configuration...${NC}"
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration test failed${NC}"
    nginx -t
    exit 1
fi

echo ""
echo -e "${YELLOW}[5/5] Reloading nginx...${NC}"
systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"

echo ""
echo -e "${GREEN}=== Server restart complete! ===${NC}"
echo ""
echo "Service status:"
systemctl status "$GUNICORN_SERVICE" --no-pager -l | head -n 15
echo ""
echo "Nginx status:"
systemctl status nginx --no-pager | head -n 5
