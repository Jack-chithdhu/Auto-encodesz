# 🚀 Deployment Guide — Auto_Encodes Bot

Before deploying on **any** platform, you'll need these credentials ready:

| Variable | Where to get it |
|---|---|
| `API_ID` / `API_HASH` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram |
| `BOT_USERNAME` | Your bot's username without `@` |
| `BASE` | Chat ID of your log group |
| `FFMPEG` | Chat ID of channel with FFmpeg executables |
| `FFMPEGID` | Space-separated message IDs of FFmpeg files (e.g. `2 3 4`) |
| `FFMPEGCMD` | Message ID of the FFmpeg command |
| `DESTINATION` | Chat ID of the output channel |

---

## 1. 🟣 Heroku (~$7/month)

> Requires a paid Heroku plan. Repo is already pre-configured.

1. Create a Heroku account at [heroku.com](https://heroku.com)
2. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. Run:
   ```bash
   heroku login
   heroku create your-app-name
   heroku stack:set container -a your-app-name
   ```
4. Set all environment variables:
   ```bash
   heroku config:set API_ID=xxx API_HASH=xxx BOT_TOKEN=xxx BOT_USERNAME=xxx \
     BASE=xxx FFMPEG=xxx FFMPEGID="2 3 4" FFMPEGCMD=5 DESTINATION=xxx \
     HEROKU_API_KEY=xxx HEROKU_APP_NAME=your-app-name -a your-app-name
   ```
5. Deploy:
   ```bash
   git push heroku main
   heroku ps:scale worker=1 -a your-app-name
   ```
6. View logs:
   ```bash
   heroku logs --tail -a your-app-name
   ```

---

## 2. 🚂 Railway (~$5/month)

> Easiest cloud option. Supports Docker natively.

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your forked repo
4. Go to **Variables** tab and add all env vars from `.env.example`
5. Railway auto-detects `railway.toml` and deploys using the Dockerfile
6. Done — Railway will redeploy automatically on every git push

---

## 3. 🎨 Render (~$7/month or free with limitations)

> Free tier exists but the bot will sleep after inactivity — not ideal.

1. Go to [render.com](https://render.com) and sign in with GitHub
2. Click **New → Blueprint** and connect your repo
3. Render will auto-detect `render.yaml` and configure the service
4. Fill in the environment variables marked `sync: false` in the Render dashboard
5. Click **Apply** to deploy

> ⚠️ Free tier workers spin down after 15 minutes of inactivity. Use the **Starter** plan ($7/month) for a persistent bot.

---

## 4. 🖥️ VPS — Recommended for encoding (from ~$4/month)

> Best performance and value for CPU-heavy video encoding workloads.

**Recommended providers:**
- [Hetzner](https://hetzner.com) — CX22 at ~€4/month (best EU value)
- [Contabo](https://contabo.com) — VPS S at ~$5/month (best raw resources)
- [DigitalOcean](https://digitalocean.com) — Basic Droplet at $6/month
- [Vultr](https://vultr.com) — Cloud Compute at $6/month

**Steps:**

1. Spin up an **Ubuntu 22.04** VPS on any provider above
2. SSH into it:
   ```bash
   ssh root@your-server-ip
   ```
3. Clone your repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Auto_Encodes.git
   cd Auto_Encodes
   ```
4. Run the setup script:
   ```bash
   chmod +x deploy_vps.sh
   ./deploy_vps.sh
   ```
5. The script will prompt you to fill in `.env`, then build and start the bot automatically.

**Useful commands after deployment:**
```bash
docker compose logs -f        # Live logs
docker compose down           # Stop bot
docker compose restart        # Restart bot
docker compose up -d --build  # Rebuild and restart after code changes
```

---

## 💡 Which should I pick?

| | Heroku | Railway | Render | VPS |
|---|---|---|---|---|
| Price | $7/mo | ~$5/mo | $7/mo | $4–6/mo |
| Setup difficulty | Easy | Easiest | Easy | Medium |
| Best for encoding | ❌ | ⚠️ | ⚠️ | ✅ |
| Always on | ✅ | ✅ | Paid only | ✅ |
| Auto-redeploy | ✅ | ✅ | ✅ | Manual |

**👉 For a video encoding bot, a VPS (Hetzner or Contabo) is the best choice.** Encoding is CPU-intensive — cloud platforms charge per-resource and will cost more for heavy use.
