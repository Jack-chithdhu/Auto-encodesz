BASE = "-1001361915166"             # MAIN BASE GROUP — bot sends log messages here
FFMPEG = "-1001514731412"           # Channel ID where FFmpeg executables are stored
DESTINATION = "-1001463218112"      # Channel/group ID where encoded output files are sent
FFMPEGID = "2 3 4"                  # Space-separated message IDs of FFmpeg executables in FFMPEG channel
FFMPEGCMD = "5"                     # Message ID of the FFmpeg command to execute

# NOTE: Your FFmpeg command (stored in Telegram at FFMPEGCMD msg ID) must follow this format:
#   Input:  ./downloads/[file]
#   Output: ./downloads/[AG] [file]   ← output file must be the last argument

# NOTE: Also set HEROKU_APP_NAME env var to your Heroku app's name (e.g. "my-encode-bot")

