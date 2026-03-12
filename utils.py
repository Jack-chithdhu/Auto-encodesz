import asyncio
import os
import re
import time
import shutil
import json
import subprocess

from FastTelethonhelper import fast_upload, fast_download
from config import bot, DESTINATION

D = str(DESTINATION).replace("-100", "")

# ── Feature 4: Persistent Queue ───────────────────────────────────────────────
QUEUE_FILE = "queue.json"

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)


# ── Feature 8: Disk Space Check ───────────────────────────────────────────────
def check_disk_space(required_mb=1500):
    """Returns (ok: bool, free_mb: int)"""
    stat = shutil.disk_usage("./downloads") if os.path.exists("./downloads") else shutil.disk_usage(".")
    free_mb = stat.free // (1024 * 1024)
    return free_mb >= required_mb, free_mb


# ── Feature 9: Duplicate Detection ───────────────────────────────────────────
def is_duplicate(filename):
    output_path = f"./downloads/[AG] {filename}"
    return os.path.exists(output_path)


# ── FFmpeg runner with live progress ─────────────────────────────────────────
# Feature 1: Progress Bar — parses FFmpeg stderr for real-time stats
# Feature 2: /cancel — exposes the process so it can be killed externally

current_ffmpeg_proc = None  # exposed for /cancel

async def run_with_progress(cmd, status_msg, input_size_mb=0):
    """Run FFmpeg and update status_msg with live progress every 5 seconds."""
    global current_ffmpeg_proc

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    current_ffmpeg_proc = proc

    stderr_lines = []
    last_edit = time.time()
    start_time = time.time()

    # Read stderr line by line for progress
    while True:
        line = await proc.stderr.readline()
        if not line:
            break
        line = line.decode("utf-8", errors="replace").strip()
        stderr_lines.append(line)

        # Parse FFmpeg progress line: frame=... fps=... size=... time=... bitrate=...
        if "time=" in line and "fps=" in line:
            now = time.time()
            if now - last_edit >= 5:  # update every 5 seconds
                try:
                    fps_match = re.search(r"fps=\s*([\d.]+)", line)
                    size_match = re.search(r"size=\s*(\d+)kB", line)
                    time_match = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
                    bitrate_match = re.search(r"bitrate=\s*([\d.]+)", line)

                    fps = fps_match.group(1) if fps_match else "?"
                    out_size_mb = int(size_match.group(1)) / 1024 if size_match else 0
                    elapsed = int(now - start_time)
                    elapsed_str = f"{elapsed // 60}m {elapsed % 60}s"

                    progress_text = f"⚙️ **Encoding in progress...**\n\n"
                    progress_text += f"🎞 FPS: `{fps}`\n"
                    if out_size_mb:
                        progress_text += f"📦 Output so far: `{out_size_mb:.1f} MB`\n"
                    if input_size_mb:
                        progress_text += f"📥 Input: `{input_size_mb:.1f} MB`\n"
                    progress_text += f"⏱ Elapsed: `{elapsed_str}`\n"
                    if bitrate_match:
                        progress_text += f"📡 Bitrate: `{bitrate_match.group(1)} kbits/s`"

                    await status_msg.edit(progress_text)
                    last_edit = now
                except:
                    pass  # Never crash the encode just because progress parsing failed

    await proc.wait()
    current_ffmpeg_proc = None

    full_stderr = "\n".join(stderr_lines)
    if proc.returncode != 0:
        return False, full_stderr[-2000:]
    return True, full_stderr[-2000:]


# ── Feature 3: Mediainfo Report ───────────────────────────────────────────────
def get_mediainfo(filepath):
    """Returns a dict with codec, resolution, bitrate, duration, size."""
    try:
        from pymediainfo import MediaInfo
        info = MediaInfo.parse(filepath)
        result = {}
        for track in info.tracks:
            if track.track_type == "General":
                result["duration"] = track.other_duration[0] if track.other_duration else "?"
                result["size_mb"] = round(os.path.getsize(filepath) / (1024 * 1024), 1)
            elif track.track_type == "Video":
                result["codec"] = track.format or "?"
                result["resolution"] = f"{track.width}x{track.height}" if track.width else "?"
                result["fps"] = track.frame_rate or "?"
            elif track.track_type == "Audio":
                result["audio"] = track.format or "?"
                result["audio_bitrate"] = f"{int(track.bit_rate) // 1000}kbps" if track.bit_rate else "?"
        return result
    except Exception as e:
        return {}

def format_mediainfo(info, label=""):
    if not info:
        return ""
    lines = [f"**{label}**"] if label else []
    if "size_mb" in info:
        lines.append(f"💾 Size: `{info['size_mb']} MB`")
    if "codec" in info:
        lines.append(f"🎬 Codec: `{info['codec']}`")
    if "resolution" in info:
        lines.append(f"📐 Resolution: `{info['resolution']}`")
    if "fps" in info:
        lines.append(f"🎞 FPS: `{info['fps']}`")
    if "audio" in info:
        lines.append(f"🔊 Audio: `{info['audio']} {info.get('audio_bitrate', '')}`")
    if "duration" in info:
        lines.append(f"⏱ Duration: `{info['duration']}`")
    return "\n".join(lines)


# ── Feature 10: Auto Thumbnail ────────────────────────────────────────────────
def extract_thumbnail(video_path, thumb_path="./downloads/thumb.jpg"):
    """Extract a frame at 10% into the video as a thumbnail."""
    try:
        # Get duration first
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True
        )
        duration = float(probe.stdout.strip())
        seek_time = duration * 0.1  # 10% into the video
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(seek_time), "-i", video_path,
             "-vframes", "1", "-q:v", "2", thumb_path],
            capture_output=True
        )
        return thumb_path if os.path.exists(thumb_path) else None
    except:
        return None


# ── Main encode function ──────────────────────────────────────────────────────
async def encode(msg, cmd, e1080=False):
    os.makedirs("./downloads", exist_ok=True)

    # Feature 8: Disk space check
    ok, free_mb = check_disk_space(required_mb=1500)
    if not ok:
        await msg.reply(f"⚠️ Not enough disk space to encode.\nFree: `{free_mb} MB` — need at least `1500 MB`.\nFree up space and try again.")
        return

    r = await msg.reply("📥 Downloading...")
    start_time = time.time()

    file = await fast_download(client=bot, msg=msg, reply=r, download_folder="./downloads/")
    file = file.split("/")[-1]
    input_path = f"./downloads/{file}"

    # Feature 9: Duplicate detection
    if is_duplicate(file):
        await r.edit(f"⚠️ `[AG] {file}` already exists in downloads.\nDelete it first with `/del ./downloads/[AG] {file}` then retry.")
        return

    # Feature 3: Mediainfo on input
    input_info = get_mediainfo(input_path)
    input_size_mb = input_info.get("size_mb", 0)

    await r.edit("⚙️ Starting encode...")

    command = cmd.text.replace('[file]', file)
    if e1080:
        command = command.replace("-vf scale=1280:720", "")

    # Derive output filename from last arg of command
    output_file = f"[AG] {file}"
    parts = command.split()
    for i, part in enumerate(parts):
        if i == len(parts) - 1 and not part.startswith('-'):
            output_file = part.split("/")[-1]

    output_path = f"./downloads/{output_file}"

    # Feature 1: Progress bar — run FFmpeg with live updates
    success, ffmpeg_log = await run_with_progress(command, r, input_size_mb=input_size_mb)

    if not success:
        await r.edit(f"❌ FFmpeg failed!\n\n`{ffmpeg_log[-1500:]}`")
        if os.path.exists(input_path):
            os.remove(input_path)
        return

    encode_time = int(time.time() - start_time)
    encode_time_str = f"{encode_time // 60}m {encode_time % 60}s"

    # Feature 3: Mediainfo on output
    output_info = get_mediainfo(output_path)
    output_size_mb = output_info.get("size_mb", 0)

    await r.edit("📤 Uploading...")

    # Feature 10: Extract thumbnail
    thumb_path = extract_thumbnail(output_path)

    res_file = await fast_upload(client=bot, file_location=output_path, reply=r)
    await r.delete()

    # Cleanup input
    if os.path.exists(input_path) and file != output_file:
        os.remove(input_path)

    # Upload to destination with thumbnail
    try:
        if thumb_path and os.path.exists(thumb_path):
            y = await bot.send_file(DESTINATION, res_file, caption=f"`{output_file}`",
                                     thumb=thumb_path, force_document=True)
        else:
            y = await bot.send_message(DESTINATION, f"`{output_file}`",
                                        file=res_file, force_document=True)
    except:
        y = await msg.reply(f"`{output_file}`", file=res_file, force_document=True)

    # Cleanup output and thumbnail
    if os.path.exists(output_path):
        os.remove(output_path)
    if thumb_path and os.path.exists(thumb_path):
        os.remove(thumb_path)

    # Feature 3: Build summary report
    saved_mb = round(input_size_mb - output_size_mb, 1) if input_size_mb and output_size_mb else "?"
    pct = round((1 - output_size_mb / input_size_mb) * 100, 1) if input_size_mb and output_size_mb else "?"

    summary = f"✅ **Encode Complete!**\n\n"
    if input_info:
        summary += format_mediainfo(input_info, "📥 Input") + "\n\n"
    if output_info:
        summary += format_mediainfo(output_info, "📤 Output") + "\n\n"
    if saved_mb != "?":
        summary += f"💾 **Saved: `{saved_mb} MB` ({pct}% smaller)**\n"
    summary += f"⏱ **Time: `{encode_time_str}`**\n"
    summary += f"🔗 t.me/c/{D}/{y.id}"

    await msg.reply(summary)
