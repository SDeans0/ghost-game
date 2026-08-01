# Ghost Game - Server Deployment Guide

## Overview

This guide covers deploying the Ghost Game application on a Linux server using:
- **Gunicorn** - Python WSGI HTTP server
- **Nginx** - Reverse proxy and web server
- **Certbot** - SSL/TLS certificate management

## Server Setup Scripts

### 1. Restart Server Script (`restart_server.sh`)

Restarts the gunicorn application and nginx web server.

**Usage:**
```bash
sudo ./restart_server.sh
```

**What it does:**
1. Stops the gunicorn systemd service
2. Optionally pulls latest code from git (commented out by default)
3. Starts the gunicorn service
4. Tests nginx configuration
5. Reloads nginx

**Before using:**
- Update `APP_DIR` variable to match your deployment path
- Update `GUNICORN_SERVICE` to match your service name

### 2. Certificate Renewal Script (`renew_certs.sh`)

Renews SSL certificates using certbot and reloads nginx.

**Usage:**
```bash
sudo ./renew_certs.sh
```

**What it does:**
1. Checks current certificate expiry date
2. Attempts to renew certificates with certbot
3. Verifies nginx configuration
4. Reloads nginx with new certificates

**Automatic Renewal:**
Add to crontab for automatic renewal (runs twice daily):
```bash
sudo crontab -e
```

Add this line:
```
30 2,14 * * * /var/www/ghost-game/renew_certs.sh >> /var/log/certbot-renewal.log 2>&1
```

## Initial Server Setup

### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, nginx, certbot
sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx

# Install git (if deploying from repository)
sudo apt install -y git
```

### 2. Deploy Application

```bash
# Create application directory
sudo mkdir -p /var/www/ghost-game
sudo chown -R $USER:$USER /var/www/ghost-game

# Clone repository (or copy files)
cd /var/www/ghost-game
# git clone <your-repo-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
flask db upgrade
```

### 3. Configure Gunicorn Service

```bash
# Create log directory
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn

# Copy systemd service file
sudo cp gunicorn-ghost-game.service /etc/systemd/system/

# Update paths in the service file if needed
sudo nano /etc/systemd/system/gunicorn-ghost-game.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable gunicorn-ghost-game
sudo systemctl start gunicorn-ghost-game

# Check status
sudo systemctl status gunicorn-ghost-game
```

### 4. Configure Nginx

```bash
# Copy nginx configuration
sudo cp nginx.config /etc/nginx/sites-available/ghost-game

# Create certbot directory for challenges
sudo mkdir -p /var/www/certbot

# Enable the site
sudo ln -s /etc/nginx/sites-available/ghost-game /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 5. Obtain SSL Certificate

```bash
# Obtain certificate using certbot
sudo certbot --nginx -d games.samandperlie.uk

# Test automatic renewal
sudo certbot renew --dry-run
```

### 6. Make Scripts Executable

```bash
cd /var/www/ghost-game
chmod +x restart_server.sh renew_certs.sh
```

## Maintenance Commands

### View Application Logs
```bash
# Gunicorn logs
sudo tail -f /var/log/gunicorn/ghost-game-error.log
sudo tail -f /var/log/gunicorn/ghost-game-access.log

# Nginx logs
sudo tail -f /var/log/nginx/games.samandperlie.uk-error.log
sudo tail -f /var/log/nginx/games.samandperlie.uk-access.log

# Systemd service logs
sudo journalctl -u gunicorn-ghost-game -f
```

### Check Service Status
```bash
# Gunicorn status
sudo systemctl status gunicorn-ghost-game

# Nginx status
sudo systemctl status nginx

# Certificate status
sudo certbot certificates
```

### Manual Service Management
```bash
# Start services
sudo systemctl start gunicorn-ghost-game
sudo systemctl start nginx

# Stop services
sudo systemctl stop gunicorn-ghost-game
sudo systemctl stop nginx

# Restart services
sudo systemctl restart gunicorn-ghost-game
sudo systemctl restart nginx

# Reload nginx (without dropping connections)
sudo systemctl reload nginx
```

## Troubleshooting

### Gunicorn won't start
1. Check logs: `sudo journalctl -u gunicorn-ghost-game -n 50`
2. Verify paths in `/etc/systemd/system/gunicorn-ghost-game.service`
3. Test manually: 
   ```bash
   cd /var/www/ghost-game
   source venv/bin/activate
   gunicorn -w 2 -b 127.0.0.1:8000 app:app
   ```

### Nginx configuration errors
1. Test config: `sudo nginx -t`
2. Check error log: `sudo tail -f /var/log/nginx/error.log`
3. Verify file permissions

### SSL certificate issues
1. Check certificate: `sudo certbot certificates`
2. Test renewal: `sudo certbot renew --dry-run`
3. Check certbot logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`

### Database issues
1. Check database file permissions
2. Run migrations: `flask db upgrade`
3. Check application logs

## Performance Tuning

### Gunicorn Workers
Adjust worker count in `gunicorn-ghost-game.service`:
- Formula: `(2 x NUM_CORES) + 1`
- Example: 4-core CPU = 9 workers

### Nginx Caching
Add to nginx.config for static file caching:
```nginx
location /static/ {
    alias /var/www/ghost-game/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## Security Recommendations

1. **Firewall**: Configure UFW to only allow ports 22, 80, 443
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Regular Updates**: Keep system and packages updated
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **SSH Key Authentication**: Disable password authentication

4. **Fail2ban**: Install to prevent brute force attacks
   ```bash
   sudo apt install fail2ban
   ```

5. **Backup**: Regularly backup database and application files

## Quick Reference

```bash
# Restart everything
sudo ./restart_server.sh

# Renew SSL certificates
sudo ./renew_certs.sh

# View live logs
sudo journalctl -u gunicorn-ghost-game -f

# Quick restart
sudo systemctl restart gunicorn-ghost-game && sudo systemctl reload nginx
```

## Environment Variables

Consider creating a `.env` file for sensitive configuration:
```bash
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///ghost_game.db
```

Update the systemd service file to load environment variables from file if needed.
