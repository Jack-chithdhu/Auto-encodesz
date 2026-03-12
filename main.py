from telethon import events
from config import app, bot, bot_username, BASE, FFMPEG, FFMPEGCMD, FFMPEGID, DESTINATION
from FastTelethonhelper import fast_upload, fast_download
import subprocess
import asyncio
import utils
import os
import shutil
import time

# Feature 4: Persistent queue — loaded from disk on startup
queue = utils.load_queue()
Locked = True

# ── Preset System ──────────────────────────────────────────────────────────────
PRESETS = {
    "quality": {
        "label": "🏆 Quality (~300MB)",
        "desc": "Best visual quality, larger file. CRF 24, slow preset.",
        "cmd": "ffmpeg -i ./downloads/[file] -c:v libx265 -crf 24 -preset slow -c:a aac -b:a 192k ./downloads/[AG] [file]"
    },
    "balanced": {
        "label": "⚖️ Balanced (~200MB)",
        "desc": "Best size/quality tradeoff. CRF 28, medium preset.",
        "cmd": "ffmpeg -i ./downloads/[file] -c:v libx265 -crf 28 -preset medium -c:a aac -b:a 128k ./downloads/[AG] [file]"
    },
    "small": {
        "label": "📦 Small (~150MB)",
        "desc": "Smaller file, slightly lower quality. CRF 30, medium preset.",
        "cmd": "ffmpeg -i ./downloads/[file] -c:v libx265 -crf 30 -preset medium -c:a aac -b:a 96k ./downloads/[AG] [file]"
    },
    "tiny": {
        "label": "🗜️ Tiny (~100MB)",
        "desc": "Maximum compression, noticeable quality loss. CRF 34, fast preset.",
        "cmd": "ffmpeg -i ./downloads/[file] -c:v libx265 -crf 34 -preset fast -c:a aac -b:a 64k ./downloads/[AG] [file]"
    },
    "h264": {
        "label": "🔄 H.264 Balanced (~250MB)",
        "desc": "Use when source is already H.265. Wider device compatibility.",
        "cmd": "ffmpeg -i ./downloads/[file] -c:v libx264 -crf 23 -preset slow -c:a aac -b:a 128k ./downloads/[AG] [file]"
    },
}
active_preset = None

# ── Feature 5: Whitelist ───────────────────────────────────────────────────────
# Add your Telegram user IDs here. Leave empty [] to allow everyone.
# Get your user ID by messaging @userinfobot on Telegram.
WHITELIST = []

def is_allowed(event):
    if not WHITELIST:
        return True
    return event.sender_id in WHITELIST

# ── Feature 14: Auto-restart on crash ─────────────────────────────────────────
bot_start_time = time.time()


loop = asyncio.get_event_loop()

async def dl_ffmpeg():
    global Locked
    message = "Starting up..."
    a = await bot.send_message(BASE, "Starting up...")
    r = await bot.send_message(BASE, "Downloading ffmpeg files now.....")
    msgs = await bot.get_messages(FFMPEG, ids=FFMPEGID)
    cmd = await bot.get_messages(FFMPEG, ids=FFMPEGCMD)
    for msg in msgs:
        s = await fast_download(bot, msg, r, "")
        subprocess.call(f"chmod 777 ./{s}", shell=True)
        message = f"{message}\n{s} Downloaded"
        await a.edit(message)
    queue_notice = f"\n\n📋 Queue restored: {len(queue)} item(s)" if queue else ""
    await r.edit(
        f"✅ FFMPEG ready.\n\nDefault command:\n`{cmd.text}`\n\n"
        f"Use /preset to switch quality presets.{queue_notice}"
    )
    Locked = False


# ── Helper: get active command ─────────────────────────────────────────────────
async def get_cmd():
    if active_preset:
        class CmdObj:
            text = PRESETS[active_preset]["cmd"]
        return CmdObj()
    return await bot.get_messages(FFMPEG, ids=FFMPEGCMD)


# ── Preset Commands ────────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/preset{bot_username}$"))
async def show_presets(event):
    if not is_allowed(event): return
    current = active_preset if active_preset else "telegram default (FFMPEGCMD)"
    text = f"**🎛️ Available Presets**\n\nCurrently active: `{current}`\n\n"
    for key, p in PRESETS.items():
        text += f"**{p['label']}**\n`/preset {key}`\n_{p['desc']}_\n\n"
    text += "**🔁 Reset to Telegram command:**\n`/preset reset`"
    await event.reply(text)

@bot.on(events.NewMessage(pattern=f"/preset{bot_username} (.+)"))
async def set_preset(event):
    if not is_allowed(event): return
    global active_preset
    if Locked:
        await event.reply("⚠️ Cannot change preset while encoding is in progress.")
        return
    arg = event.pattern_match.group(1).strip().lower()
    if arg == "reset":
        active_preset = None
        await event.reply("✅ Reset to default Telegram FFMPEGCMD command.")
        return
    if arg not in PRESETS:
        keys = ", ".join(f"`{k}`" for k in PRESETS)
        await event.reply(f"❌ Unknown preset `{arg}`.\n\nAvailable: {keys}")
        return
    active_preset = arg
    p = PRESETS[arg]
    await event.reply(
        f"✅ Preset set to **{p['label']}**\n\n_{p['desc']}_\n\n"
        f"Command:\n`{p['cmd']}`"
    )


# ── Encode ─────────────────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/encode{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    global Locked
    if Locked:
        await event.reply("⏳ Bot is busy encoding. Use /addq to queue it.")
        return
    Locked = True
    try:
        msg = await event.get_reply_message()
        if not msg:
            await event.reply("❌ Please reply to a file to encode.")
            Locked = False
            return
        cmd = await get_cmd()
        if active_preset:
            await event.reply(f"🎛️ Using preset: {PRESETS[active_preset]['label']}")
        e1080 = '-1080' in event.text
        await utils.encode(msg, cmd, e1080)
    except Exception as e:
        await event.reply(f"❌ Encode failed:\n`{e}`")
    Locked = False


# ── Feature 2: /cancel ────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/cancel{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    global Locked
    proc = utils.current_ffmpeg_proc
    if proc and proc.returncode is None:
        proc.terminate()
        await asyncio.sleep(1)
        if proc.returncode is None:
            proc.kill()
        Locked = False
        await event.reply("🛑 Encoding cancelled.")
    else:
        await event.reply("ℹ️ No encode is currently running.")


# ── Feature 13: /stats ────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/stats{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    uptime_sec = int(time.time() - bot_start_time)
    uptime_str = f"{uptime_sec // 3600}h {(uptime_sec % 3600) // 60}m {uptime_sec % 60}s"
    disk = shutil.disk_usage(".")
    total_gb = disk.total / (1024**3)
    used_gb = disk.used / (1024**3)
    free_gb = disk.free / (1024**3)
    preset_info = PRESETS[active_preset]['label'] if active_preset else "Telegram default"
    dl_count = len([f for f in os.listdir("./downloads")]) if os.path.exists("./downloads") else 0
    await event.reply(
        f"📊 **Bot Stats**\n\n"
        f"⏱ Uptime: `{uptime_str}`\n"
        f"🎛 Active preset: `{preset_info}`\n"
        f"📋 Queue length: `{len(queue)}`\n"
        f"🔒 Encoding now: `{'Yes' if Locked else 'No'}`\n\n"
        f"💽 **Disk Usage**\n"
        f"Total: `{total_gb:.1f} GB`\n"
        f"Used:  `{used_gb:.1f} GB`\n"
        f"Free:  `{free_gb:.1f} GB`\n\n"
        f"📁 Files in downloads: `{dl_count}`"
    )


# ── Feature 15: /logs ─────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/logs{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    try:
        p = subprocess.Popen("journalctl -u auto-encodes --no-pager -n 50 2>/dev/null || tail -n 50 bot.log 2>/dev/null || echo 'No log file found.'",
                             stdout=subprocess.PIPE, shell=True)
        out = p.communicate()[0].decode("utf-8", "replace").strip()
        await event.reply(f"```\n{out[-3000:]}\n```")
    except Exception as e:
        await event.reply(f"❌ Could not fetch logs: `{e}`")


# ── Feature 6: Auto-queue from channel ───────────────────────────────────────
# Set AUTO_QUEUE_SOURCE to a channel ID to auto-add all new files posted there.
AUTO_QUEUE_SOURCE = None  # e.g. -1001234567890  — set via /setautoqueue

@bot.on(events.NewMessage)
async def auto_queue_listener(event):
    if AUTO_QUEUE_SOURCE and event.chat_id == AUTO_QUEUE_SOURCE:
        if event.document or event.video:
            queue.append(event.id)
            utils.save_queue(queue)
            await bot.send_message(BASE, f"📥 Auto-queued message ID `{event.id}` from source channel.\nQueue length: `{len(queue)}`")

@bot.on(events.NewMessage(pattern=f"/setautoqueue{bot_username}"))
async def set_auto_queue(event):
    if not is_allowed(event): return
    global AUTO_QUEUE_SOURCE
    args = event.raw_text.split()
    if len(args) < 2:
        current = f"`{AUTO_QUEUE_SOURCE}`" if AUTO_QUEUE_SOURCE else "not set"
        await event.reply(
            f"📡 **Auto-Queue Source**\n\nCurrently: {current}\n\n"
            f"Usage: `/setautoqueue CHANNEL_ID`\n"
            f"To disable: `/setautoqueue off`"
        )
        return
    if args[1].lower() == "off":
        AUTO_QUEUE_SOURCE = None
        await event.reply("✅ Auto-queue disabled.")
    else:
        try:
            AUTO_QUEUE_SOURCE = int(args[1])
            await event.reply(f"✅ Auto-queue enabled.\nWatching channel: `{AUTO_QUEUE_SOURCE}`\nAll new files will be added to the queue automatically.")
        except:
            await event.reply("❌ Invalid channel ID. Use a numeric ID like `-1001234567890`.")


# ── Basic Commands ─────────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/start{bot_username}"))
async def _(event):
    preset_info = PRESETS[active_preset]['label'] if active_preset else "telegram default"
    whitelist_info = f"{len(WHITELIST)} user(s)" if WHITELIST else "open (no whitelist)"
    await event.reply(
        f"✅ **I'm alive!**\n\n"
        f"🎛 Active preset: `{preset_info}`\n"
        f"📋 Queue: `{len(queue)} item(s)`\n"
        f"🔐 Whitelist: `{whitelist_info}`\n\n"
        f"Commands: /preset /encode /addq /sq /cancel /stats /logs /setautoqueue"
    )

@bot.on(events.NewMessage(pattern=f"/ls{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    p = subprocess.Popen('ls -lh downloads', stdout=subprocess.PIPE, shell=True)
    x = await event.reply(p.communicate()[0].decode("utf-8", "replace").strip() or "📁 downloads/ is empty")
    await asyncio.sleep(15)
    await x.delete()

@bot.on(events.NewMessage(pattern=f"/up{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    path = event.raw_text.split(' ', 1)[-1]
    r = await event.reply("📤 Uploading...")
    res_file = await fast_upload(bot, path, r)
    try:
        await bot.send_message(DESTINATION, file=res_file, force_document=True)
    except:
        await event.reply(file=res_file, force_document=True)

@bot.on(events.NewMessage(pattern=f"/del{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    path = event.raw_text.split(' ', 1)[-1]
    try:
        os.remove(path)
        await event.reply("🗑 Deleted.")
    except Exception as e:
        await event.reply(str(e))


# ── Queue Commands ─────────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/addq{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    if Locked:
        await event.reply("⚠️ Cannot update queue while encoding is in progress.")
        return
    msg = await event.get_reply_message()
    queue.append(msg.id)
    utils.save_queue(queue)
    await event.reply(f"✅ Added to queue.\n📋 Queue ({len(queue)} items): `{queue}`")

@bot.on(events.NewMessage(pattern=f"/aq{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    args = event.raw_text.split(" ")
    msg = await event.get_reply_message()
    count = int(args[1]) if len(args) > 1 else 5
    for i in range(msg.id, msg.id + count):
        queue.append(i)
    utils.save_queue(queue)
    await event.reply(f"✅ Added {count} items to queue.\n📋 Queue ({len(queue)} items): `{queue}`")

@bot.on(events.NewMessage(pattern=f"/clearq{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    if Locked:
        await event.reply("⚠️ Cannot clear queue while encoding is in progress.")
        return
    global queue
    queue = []
    utils.save_queue(queue)
    await event.reply("✅ Queue cleared.")

@bot.on(events.NewMessage(pattern=f"/sq{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    global Locked, queue
    if Locked:
        await event.reply("⏳ Bot is already encoding.")
        return
    if not queue:
        await event.reply("📋 Queue is empty.")
        return
    Locked = True
    await event.reply(f"▶️ Starting queue — {len(queue)} item(s) to encode.")
    for i in list(queue):
        try:
            msg = await bot.get_messages(event.chat_id, ids=i)
            cmd = await get_cmd()
            await utils.encode(msg, cmd)
            queue.remove(i)
            utils.save_queue(queue)
        except Exception as e:
            await event.reply(f"⚠️ `[{i}]` skipped:\n`{e}`")
            queue.remove(i)
            utils.save_queue(queue)
    await event.reply("✅ Queue complete.")
    Locked = False

@bot.on(events.NewMessage(pattern=f"/qstatus{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    if not queue:
        await event.reply("📋 Queue is empty.")
        return
    text = f"📋 **Queue — {len(queue)} item(s)**\n\n"
    for idx, msg_id in enumerate(queue, 1):
        text += f"`{idx}.` Message ID: `{msg_id}`\n"
    text += f"\n🔒 Encoding now: `{'Yes' if Locked else 'No'}`"
    await event.reply(text)


# ── Bot Control ────────────────────────────────────────────────────────────────

@bot.on(events.NewMessage(pattern=f"/restart{bot_username}"))
async def _(event):
    if not is_allowed(event): return
    try:
        app.restart()
    except Exception as e:
        await event.reply(str(e))


# ── Start ──────────────────────────────────────────────────────────────────────

loop.run_until_complete(dl_ffmpeg())
bot.start()
bot.run_until_disconnected()
