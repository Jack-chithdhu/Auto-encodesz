import os
import heroku3
from telethon import TelegramClient

api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')
bot_username = os.environ.get('BOT_USERNAME')
heroku_key = os.environ.get('HEROKU_API_KEY')
heroku_app_name = os.environ.get('HEROKU_APP_NAME')  # Added: required to identify app by name

BASE = os.environ.get('BASE')
if not BASE:
    from sample_config import BASE as b
    BASE = b

FFMPEG = os.environ.get('FFMPEG')
if not FFMPEG:
    from sample_config import FFMPEG as f
    FFMPEG = f  # Fix: removed premature int() — done uniformly below

DESTINATION = os.environ.get('DESTINATION')
if not DESTINATION:
    from sample_config import DESTINATION as d
    DESTINATION = d  # Fix: removed premature int() — done uniformly below

FFMPEGID = os.environ.get('FFMPEGID')
if not FFMPEGID:
    from sample_config import FFMPEGID as f
    FFMPEGID = f

FFMPEGID = FFMPEGID.split()
for i in range(len(FFMPEGID)):
    FFMPEGID[i] = int(FFMPEGID[i])

FFMPEGCMD = os.environ.get('FFMPEGCMD')
if not FFMPEGCMD:
    from sample_config import FFMPEGCMD as c
    FFMPEGCMD = c  # Fix: removed premature int() — done uniformly below

BASE = int(BASE)
FFMPEG = int(FFMPEG)
FFMPEGCMD = int(FFMPEGCMD)
DESTINATION = int(DESTINATION)

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Fix: original code used undefined variable 'herokuapp' — renamed to heroku_conn
# Fix: using app name instead of index [0] which was fragile
heroku_conn = heroku3.from_key(heroku_key)
app = heroku_conn.apps()[heroku_app_name]