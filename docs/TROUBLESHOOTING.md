
# 🐛 Troubleshooting

## Backend Not Starting

```bash
journalctl -u nettap-backend -n 50 --no-pager
```

Common issues:
- **Port already in use**: Change port in `.env`
- **Database error**: Delete `data/vpn.db` and restart
- **Import error**: Reinstall requirements: `cd /opt/nettap/backend && source venv/bin/activate && pip install -r requirements.txt`

## Telegram Bot Not Working

1. Check bot token in Settings → Telegram
2. Test proxy: Bot Manager → Test Proxy
3. Check logs: `journalctl -u nettap-bot -n 50`
4. In Iran, you MUST use a Cloudflare Worker proxy

## DNS Not Resolving

```bash
dig @YOUR_SERVER_IP test.yourdomain.com
```

If timeout:
- Check port 53: `ss -tulpn | grep :53`
- Check firewall: `ufw status`
- Check CoreDNS: `systemctl status coredns`

## SSL Certificate Issues

```bash
certbot renew --dry-run
```

If failed, use self-signed:
```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /etc/ssl/nettap/key.pem -out /etc/ssl/nettap/cert.pem -subj "/CN=yourdomain.com"
```

## Subscription Not Loading in VPN Apps

- Clear app cache and re-add subscription
- Try `?format=raw` at end of subscription URL
- Check if backend is running: `curl http://127.0.0.1:8734/`

## Reset Everything

```bash
nettap admin reset
systemctl restart nettap-backend nettap-bot
```

## Full Reinstall

```bash
nettap uninstall
bash <(curl -sSL https://raw.githubusercontent.com/tahasite/nettap/main/scripts/install.sh)
```

## Support

- Telegram: [@tahasite_chanel](https://t.me/tahasite_chanel)
- GitHub Issues: [github.com/tahasite/nettap/issues](https://github.com/tahasite/nettap/issues)
