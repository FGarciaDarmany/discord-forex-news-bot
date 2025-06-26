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
bot = commands.Bot(command_prefix="!", intents=intents)

# === FLASK APP ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot en línea y funcionando correctamente."

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
            print(f"❌ Error al enviar DM a {user_id}: {e}")

# === SCRAPING FUNCIONES ===

def get_ff_calendar():
    try:
        url = "https://www.forexfactory.com/calendar"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.content, "html.parser")
        events = []
        for row in soup.select("tr.calendar_row"):
            impact = row.get("class", [])
            if "high" in impact:
                time = row.select_one(".time").get_text(strip=True)
                currency = row.select_one(".currency").get_text(strip=True)
                event = row.select_one(".event").get_text(strip=True)
                events.append(f"**{time}** - {currency} | 🔥 {event}")
        return events
    except Exception as e:
        print("❌ Error en calendario FF:", e)
        return []

def get_ff_news():
    global last_news_title
    try:
        url = "https://www.forexfactory.com/news"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        alerts = []
        for item in soup.select(".article"):
            title = item.select_one(".title").get_text(strip=True)
            if title != last_news_title and "high impact" in title.lower():
                last_news_title = title
                alerts.append(f"{title} – https://www.forexfactory.com{item.a['href']}")
        return alerts
    except Exception as e:
        print("❌ Error en noticias FF:", e)
        return []

# === EVENTOS Y TAREAS ===

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    if not send_daily.is_running():
        send_daily.start()
    if not monitor_news.is_running():
        monitor_news.start()

@tasks.loop(hours=24)
async def send_daily():
    now = datetime.datetime.now().hour
    if now == 6:
        eventos = get_ff_calendar()
        if eventos:
            msg = "📅 **Calendario Diario:**\n" + "\n".join(eventos)
            await bot.get_channel(CALENDAR_CHANNEL_ID).send(msg)
            await send_dm(msg)

@tasks.loop(minutes=5)
async def monitor_news():
    noticias = get_ff_news()
    for n in noticias:
        texto = f"🚨 {n}"
        await bot.get_channel(NEWS_CHANNEL_ID).send(texto)
        await send_dm(texto)

# === COMANDOS ===

@bot.command()
async def suscribirme(ctx):
    if ctx.author.id not in USERS_DM:
        USERS_DM.append(ctx.author.id)
        save_subscribers()
        await ctx.send("✅ ¡Te has suscrito para recibir alertas por DM!")
    else:
        await ctx.send("Ya estás suscrito.")

@bot.command()
async def cancelarsuscripcion(ctx):
    if ctx.author.id in USERS_DM:
        USERS_DM.remove(ctx.author.id)
        save_subscribers()
        await ctx.send("❌ Has cancelado tu suscripción.")
    else:
        await ctx.send("No estabas suscrito.")

# === INICIO ===

def run_bot():
    if not TOKEN:
        print("❗ ERROR: DISCORD_TOKEN no definido")
    else:
        bot.run(TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_bot, name="DiscordBotThread").start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
