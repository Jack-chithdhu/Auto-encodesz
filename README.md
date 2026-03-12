# 🎬 Auto_Encodes Bot

A Telegram bot that automatically downloads video files, re-encodes them using FFmpeg (H.265/HEVC) to reduce file size by up to 70% while maintaining visual quality, and uploads the result to a destination channel.

> **700MB input → ~200MB output at the same perceived quality**

---

## ✨ Features

| Feature | Command |
|---|---|
| Encode a video | `/encode` (reply to file) |
| Encode at 1080p | `/encode -1080` |
| Switch quality preset | `/preset balanced` |
| Cancel ongoing encode | `/cancel` |
| Add to queue | `/addq` |
| Start queue | `/sq` |
| Queue status | `/qstatus` |
| Auto-queue from channel | `/setautoqueue CHANNEL_ID` |
| Bot stats & disk usage | `/stats` |
| List downloads folder | `/ls` |
| Upload a file manually | `/up <path>` |
| Delete a file | `/del <path>` |
| View logs | `/logs` |
| Restart bot | `/restart` |

---

## 🎛️ Quality Presets

Switch presets anytime with `/preset <name>` — no redeployment needed.

| Preset | Command | Output Size | Notes |
|---|---|---|---|
| Quality | `/preset quality` | ~300MB | CRF 24, best visual quality |
| Balanced | `/preset balanced` | ~200MB | CRF 28, recommended default |
| Small | `/preset small` | ~150MB | CRF 30, slightly lower quality |
| Tiny | `/preset tiny` | ~100MB | CRF 34, maximum compression |
| H.264 | `/preset h264` | ~250MB | Use if source is already H.265 |
| Reset | `/preset reset` | — | Use your Telegram FFMPEGCMD |

---

## 📊 Encode Summary

After every encode, the bot sends a full report:

```
✅ Encode Complete!

📥 Input
💾 Size: 698.4 MB
🎬 Codec: AVC
📐 Resolution: 1920x1080
🎞 FPS: 23.976
🔊 Audio: AAC 192kbps
⏱ Duration: 1h 42m

📤 Output
💾 Size: 201.2 MB
🎬 Codec: HEVC
📐 Resolution: 1920x1080
🎞 FPS: 23.976
🔊 Audio: AAC 128kbps

💾 Saved: 497.2 MB (71.2% smaller)
⏱ Time: 12m 34s
```

---

## 🚀 Deployment

See [DEPLOY.md](DEPLOY.md) for full step-by-step instructions for all platforms.

### Quick options:

| Platform | Cost | Best for |
|---|---|---|
| **VPS** (Hetzner/Contabo) | ~$4–6/mo | ✅ Encoding workloads |
| **Railway** | ~$5/mo | Easy cloud deploy |
| **Render** | $7/mo | Auto-deploy from GitHub |
| **Heroku** | $7/mo | Already pre-configured |

**Recommended: VPS** — encoding is CPU-intensive. Fixed price, dedicated resources.

```bash
# VPS one-liner setup
git clone https://github.com/YOUR_USERNAME/Auto_Encodes.git
cd Auto_Encodes
chmod +x deploy_vps.sh && ./deploy_vps.sh
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in your values:

| Variable | Description | Where to get |
|---|---|---|
| `API_ID` | Telegram API ID | [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Telegram API Hash | [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | Bot token | [@BotFather](https://t.me/BotFather) |
| `BOT_USERNAME` | Bot username (no @) | @BotFather |
| `BASE` | Log group chat ID | Your group |
| `FFMPEG` | Channel ID with FFmpeg files | Your channel |
| `FFMPEGID` | Space-separated message IDs of FFmpeg binaries | e.g. `2 3 4` |
| `FFMPEGCMD` | Message ID of default FFmpeg command | e.g. `5` |
| `DESTINATION` | Output channel/group ID | Your channel |
| `HEROKU_API_KEY` | Heroku API key | Heroku dashboard (only for /restart) |
| `HEROKU_APP_NAME` | Heroku app name | Heroku dashboard (only for /restart) |

---

## 🔐 Whitelist (Optional)

To restrict bot access to specific users, edit `main.py`:

```python
# Add Telegram user IDs — get yours by messaging @userinfobot
WHITELIST = [123456789, 987654321]
```

Leave as `WHITELIST = []` to allow everyone.

---

## 📡 Auto-Queue from Channel

Monitor a source channel and automatically encode every new file posted:

```
/setautoqueue -1001234567890    # Enable (use your channel ID)
/setautoqueue off               # Disable
```

---

## 🔧 FFmpeg Command Format

The FFmpeg command stored in your Telegram channel must follow this format:

```bash
ffmpeg -i ./downloads/[file] -c:v libx265 -crf 28 -preset medium -c:a aac -b:a 128k ./downloads/[AG] [file]
```

- `[file]` → replaced with the actual input filename at runtime
- Output **must** be the last argument
- Output path **must** start with `./downloads/`

---

## 📦 Requirements

- Python 3.10+
- FFmpeg with `libx265` support (included in Docker image)
- `pymediainfo` (for encode summary reports)
- Telegram API credentials

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🐳 Docker

```bash
docker compose up -d --build     # Start
docker compose logs -f           # Live logs
docker compose down              # Stop
docker compose restart           # Restart
```

---

## 📁 Project Structure

```
Auto_Encodes/
├── main.py           # Bot commands and event handlers
├── utils.py          # Encode logic, progress bar, mediainfo, thumbnail
├── config.py         # Environment variable loading
├── sample_config.py  # Default config values
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker image definition
├── docker-compose.yml# VPS deployment
├── heroku.yml        # Heroku deployment
├── railway.toml      # Railway deployment
├── render.yaml       # Render deployment
├── deploy_vps.sh     # One-click VPS setup script
├── .env.example      # Environment variable template
└── DEPLOY.md         # Full deployment guide
```

---

## 📜 License

MIT — free to use, modify and deploy.
