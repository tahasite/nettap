# 📖 NETtap Installation Guide

## Requirements

- **OS**: Ubuntu 20.04/22.04/24.04 or Debian 11/12
- **RAM**: Minimum 1GB (2GB recommended)
- **CPU**: 1 core minimum
- **Disk**: 5GB free space
- **Access**: Root access required
- **Network**: Public IP address
- **Domain**: At least one domain (two recommended)

## Quick Install

```bash
bash <(curl -sSL https://raw.githubusercontent.com/tahasite/nettap/main/scripts/install.sh)
```

## What the Installer Does

1. Checks system requirements
2. Installs Python 3, Nginx, CoreDNS
3. Downloads NETtap from GitHub
4. Creates Python virtual environments
5. Downloads frontend libraries (Tailwind, FontAwesome, Vazir font)
6. Asks for configuration (domains, admin credentials)
7. Sets up SSL certificate (Let's Encrypt)
8. Configures all services (systemd)
9. Opens firewall ports (22, 80, 443, 53)
10. Creates admin user
11. Starts all services

## Domain Setup

### Minimum: One Domain
- Panel domain (e.g., `panel.example.com`)
- Point A record to your server IP

### Recommended: Two Domains
- Panel domain: `panel.example.com` → Server IP
- DNS domain: `dns.example.com`
  - In your domain registrar, set NS records:
  - `ns1.dns.example.com` → Server IP (Glue Record)
  - `ns2.dns.example.com` → Server IP (Glue Record)

## Post-Installation

1. **Login to Panel**: `https://panel.example.com/admin/`
2. **Add Seller Subscriptions**: Settings → Seller Subs
3. **Configure Telegram Bot** (optional): Settings → Telegram
4. **Create Plans**: Plans → Add or use defaults

## CLI Commands

```bash
nettap              # Open menu
nettap status       # Check services
nettap restart      # Restart all
nettap logs         # View logs
nettap update       # Update
nettap backup       # Create backup
nettap admin reset  # Reset admin password
nettap uninstall    # Remove NETtap
```

## Updating

```bash
nettap update
```

Or manually:
```bash
bash <(curl -sSL https://raw.githubusercontent.com/tahasite/nettap/main/scripts/update.sh)
```
