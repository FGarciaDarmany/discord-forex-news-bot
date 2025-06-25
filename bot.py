import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CALENDAR_CHANNEL_ID = int(os.getenv("CALENDAR_CHANNEL_ID"))
NEWS_CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID"))
SUBSCRIBERS_FILE = "subscribers.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
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
            print(f"Error DM {user_id}: {e}")

def get_ff_calendar(period="today"):
    url = "https://www.forexfactory.com/calendar"
    res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    soup = BeautifulSoup(res.content, "html.parser")
    events = []
    rows = soup.select("tr.calendar_row")
    for row in rows:
        impact = row.get("class", [])
        if "high" in impact:
            time = row.select_one(".time").get_text(strip=True)
            currency = row.select_one(".currency").get_text(strip=True)
            event = row.select_one(".event").get_text(strip=True)
            events.append(f"**{time}** - {currency} | 🔥 {event}")
    return events

def get_investing_calendar():
    url = "https://www.investing.com/economic-calendar/"
    res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    soup = BeautifulSoup(res.content, "html.parser")
    data = []
    for row in soup.select("tr.js-event-item"):
        impact = row.select_one(".js-countries").get("title","").lower()
        if "high" in impact:
            time = row.select_one(".time").get_text(strip=True)
            event = row.select_one(".event").get_text(strip=True)
            data.append(f"**{time}** | 🔥 {event}")
    return data

def get_ff_news():
    global last_news_title
    url = "https://www.forexfactory.com/news"
    res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    alerts = []
    for item in soup.select(".article"):
        title = item.select_one(".title").get_text(strip=True)
        if title != last_news_title and "high impact" in title.lower():
            last_news_title = title
            alerts.append(f"{title} – https://www.forexfactory.com{item.a['href']}")
    return alerts

@bot.event
async def on_ready():
    print("Bot conectado:", bot.user)
    send_daily.start()
    send_weekly.start()
    check_news.start()
    monitor_live_news.start()

@tasks.loop(hours=24)
async def send_daily():
    now = datetime.datetime.now().hour
    if now == 6:
        cal1 = get_ff_calendar()
        cal2 = get_investing_calendar()
        msg = "📅 **Calendario Diario:**\n" + "\n".join(cal1 + cal2)
        await bot.get_channel(CALENDAR_CHANNEL_ID).send(msg)
        await send_dm(msg)

@tasks.loop(hours=24)
async def send_weekly():
    if datetime.datetime.now().weekday() == 0 and datetime.datetime.now().hour == 6:
        cal1 = get_ff_calendar()
        cal2 = get_investing_calendar()
        msg = "📅 **Calendario Diario:**\n" + "\n".join(cal1 + cal2)
        await bot.get_channel(CALENDAR_CHANNEL_ID).send(msg)
        await send_dm(msg)

@tasks.loop(minutes=5)
async def check_news():
    alerts = get_ff_calendar()
    if alerts:
        msg = "⚠️ **Próximas noticias de alto impacto:**\n" + "\n".join(alerts)
        await bot.get_channel(NEWS_CHANNEL_ID).send(msg)
        await send_dm(msg)

@tasks.loop(minutes=5)
async def monitor_live_news():
    alerts = get_ff_news()
    for a in alerts:
        await bot.get_channel(NEWS_CHANNEL_ID).send("🚨 " + a)
        await send_dm("🚨 " + a)

@bot.command()
async def suscribirme(ctx):
    if ctx.author.id not in USERS_DM:
        USERS_DM.append(ctx.author.id)
        save_subscribers()
        await ctx.send("¡Subscrito por DM!")
    else:
        await ctx.send("Ya estás suscrito.")

@bot.command()
async def cancelarsuscripcion(ctx):
    if ctx.author.id in USERS_DM:
        USERS_DM.remove(ctx.author.id)
        save_subscribers()
        await ctx.send("Te has dado de baja.")
    else:
        await ctx.send("No estás suscrito.")

bot.run(TOKEN)
