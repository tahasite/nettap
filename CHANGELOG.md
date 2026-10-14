# Changelog

All notable changes to NETtap will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

### 🎉 Initial Release

#### Added
- Smart DNS-based VPN subscription panel
- CoreDNS integration for local DNS management
- Full admin panel with three languages (EN/FA/RU)
- Telegram bot with auto-setup wizard
- User subscription management with time-based plans
- Config groups system
- Force join channels for Telegram bot
- Receipt-based payment system
- Referral system with 20% commission
- Free trial system with phone verification
- QR code generation for subscriptions
- Cron jobs for automation
- Dark/Light theme switcher
- Mobile responsive design
- One-command installation script
- CLI management tool (`nettap`)
- Dynamic settings system
- Dynamic branding support
- Backup and restore utilities

#### Core Features
- Zero bandwidth usage (DNS-only proxy)
- Instant user blocking
- Multi-seller subscription support
- Auto IP resolution and country detection
- Ping testing for all configs
- Pinned configs for VIP users
- Timer starts on first user connection
- Automatic subscription expiry

#### Technical
- FastAPI backend with async support
- SQLAlchemy ORM
- SQLite database (easily extensible)
- APScheduler for background jobs
- JWT authentication
- Nginx reverse proxy with SSL
- Systemd service management
- Cloudflare Workers proxy support for Telegram API

[1.0.0]: https://github.com/tahasite/nettap/releases/tag/v1.0.0