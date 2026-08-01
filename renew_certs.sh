#!/bin/bash
# Script to renew SSL certificates with certbot and reload nginx
# Usage: sudo ./renew_certs.sh
# Recommended: Add to crontab for automatic renewal
# Example crontab entry (runs twice daily at 2:30 AM and 2:30 PM):
# 30 2,14 * * * /var/www/ghost-game/renew_certs.sh >> /var/log/certbot-renewal.log 2>&1

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== SSL Certificate Renewal Script ===${NC}"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

# Domain to renew
DOMAIN="games.samandperlie.uk"

echo -e "${YELLOW}[1/3] Checking certificate expiry...${NC}"
if [ -f "/etc/letsencrypt/live/$DOMAIN/cert.pem" ]; then
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/cert.pem" | cut -d= -f2)
    EXPIRY_EPOCH=$(date -j -f "%b %d %T %Y %Z" "$EXPIRY_DATE" "+%s" 2>/dev/null || date -d "$EXPIRY_DATE" "+%s" 2>/dev/null)
    CURRENT_EPOCH=$(date "+%s")
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
    
    echo -e "${BLUE}Current certificate expires: $EXPIRY_DATE${NC}"
    echo -e "${BLUE}Days remaining: $DAYS_LEFT${NC}"
    
    if [ $DAYS_LEFT -gt 30 ]; then
        echo -e "${GREEN}✓ Certificate is still valid for more than 30 days${NC}"
        echo -e "${YELLOW}⚠ Renewal not necessary, but will attempt anyway...${NC}"
    else
        echo -e "${YELLOW}⚠ Certificate expires in $DAYS_LEFT days - renewal recommended${NC}"
    fi
else
    echo -e "${RED}✗ Certificate not found at /etc/letsencrypt/live/$DOMAIN/cert.pem${NC}"
    echo -e "${YELLOW}⚠ Will attempt to obtain new certificate...${NC}"
fi

echo ""
echo -e "${YELLOW}[2/3] Renewing certificate with certbot...${NC}"

# Attempt renewal
if certbot renew --quiet --deploy-hook "systemctl reload nginx"; then
    echo -e "${GREEN}✓ Certificate renewal successful${NC}"
    
    # Check if certificate was actually renewed
    if [ -f "/etc/letsencrypt/live/$DOMAIN/cert.pem" ]; then
        NEW_EXPIRY_DATE=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/cert.pem" | cut -d= -f2)
        echo -e "${GREEN}New certificate expires: $NEW_EXPIRY_DATE${NC}"
    fi
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ No renewal needed - certificates are up to date${NC}"
    else
        echo -e "${RED}✗ Certificate renewal failed with exit code $EXIT_CODE${NC}"
        exit $EXIT_CODE
    fi
fi

echo ""
echo -e "${YELLOW}[3/3] Verifying nginx configuration and reloading...${NC}"

# Test nginx configuration
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
    
    # Reload nginx to use new certificates
    systemctl reload nginx
    echo -e "${GREEN}✓ Nginx reloaded with updated certificates${NC}"
else
    echo -e "${RED}✗ Nginx configuration test failed${NC}"
    nginx -t
    exit 1
fi

echo ""
echo -e "${GREEN}=== Certificate renewal complete! ===${NC}"
echo ""

# Display certificate info
echo -e "${BLUE}Certificate information for $DOMAIN:${NC}"
certbot certificates -d "$DOMAIN" 2>/dev/null | grep -A 5 "Certificate Name: $DOMAIN" || echo "Could not retrieve certificate details"

echo ""
echo -e "${YELLOW}Note: Certbot will only renew certificates that expire in less than 30 days.${NC}"
echo -e "${YELLOW}To force renewal regardless of expiry date, run:${NC}"
echo -e "${BLUE}certbot renew --force-renewal${NC}"
