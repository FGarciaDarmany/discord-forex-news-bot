import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
from flask import Flask
import threading

# === VARIABLES DE ENTORNO ===
TOKEN = os.getenv("DISCORD_TOKEN")
CALENDAR_CHANNEL_ID = int(os.getenv("CALENDAR_CHANNEL_ID", "0"))
NEWS_CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID", "0"))
SUBSCRIBERS_FILE = "subscribers.json"

# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === FLASK APP ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo y escuchando..."

# === SUBSCRIPTORES ===
last_news_title = None

if os.path.exists(SUBSCRIBERS_FILE):
    with open(SUBSCRIBERS_FILE, "r") as f:
        USERS_DM = json.load(f)
else:
    USERS_DM = []

def save_subscribers():
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(USERS_DM, f)

async def send_dm(message):
    for user_id in USERS_DM:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(message)
        except Exception as e:
            print(f"Error al enviar DM a {user_id}: {e}")