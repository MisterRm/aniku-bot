# Aniku Telegram Bot

Bot Telegram untuk channel Dayynime dengan fitur inline menu.

## Setup

1. Deploy ke Vercel
2. Tambah environment variable `TELEGRAM_BOT_TOKEN`
3. Set webhook:
```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<domain-vercel>/webhook
```

## Commands
- `/start` atau `/menu` — tampilkan menu utama

## Menu
- 📦 Versi Terbaru — info release terbaru dari GitHub
- 📋 Semua Versi — list semua versi yang pernah rilis
- 📲 Download — link download APK
