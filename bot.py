import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
from flask import Flask
import threading

# === VARIABLES DE ENTORNO Y CANALES ===
TOKEN = os.getenv("DISCORD_TOKEN")
EURUSD_CHANNEL_ID = 1387745037944881193
DXY_CHANNEL_ID = 1387745143993401495
XAUUSD_CHANNEL_ID = 1387745575734218782
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

# === ESTACIONALIDAD Y MOOD ===

def generar_estacionalidad(activo):
    estacionales = {
        "eurusd": (
            "📆 **Estacionalidad de JUNIO – EUR/USD**\n"
            "Históricamente junio es un mes alcista 📈\n"
            "▪️ Promedio: +0.75%\n"
            "▪️ Probabilidad de cierre positivo: 68%\n"
            "▪️ Datos: 10 años (2014–2024)"
        ),
        "xauusd": (
            "📆 **Estacionalidad de JUNIO – XAU/USD**\n"
            "Junio suele ser un mes de consolidación para el oro 🟡\n"
            "▪️ Promedio: +0.22%\n"
            "▪️ Probabilidad de cierre positivo: 52%\n"
            "▪️ Datos: 10 años (2014–2024)"
        ),
        "dxy": (
            "📆 **Estacionalidad de JUNIO – DXY**\n"
            "El índice del dólar tiende a debilitarse ligeramente en junio 📉\n"
            "▪️ Promedio: -0.35%\n"
            "▪️ Probabilidad de cierre positivo: 41%\n"
            "▪️ Datos: 10 años (2014–2024)"
        )
    }
    return estacionales.get(activo)

def generar_mood(activo):
    moods = {
        "eurusd": (
            "🔵 **Market Mood (Forecaster.biz)**\n"
            "Estado: Sobrecompra ⚠️\n"
            "▪️ DPO: 69.4 | Wyckoff: 113.2 | Speed: 48.1\n"
            "👉 Posible corrección si no sostiene zona clave"
        ),
        "xauusd": (
            "🔵 **Market Mood (Forecaster.biz)**\n"
            "Estado: Neutro ⚖️\n"
            "▪️ DPO: 52.3 | Wyckoff: 98.2 | Speed: 37.1\n"
            "👉 Mercado en equilibrio con sesgo ligeramente alcista"
        ),
        "dxy": (
            "🔵 **Market Mood (Forecaster.biz)**\n"
            "Estado: Sobreventa 🛑\n"
            "▪️ DPO: 31.9 | Wyckoff: 72.5 | Speed: 25.8\n"
            "👉 Posible rebote técnico si mantiene zona de soporte"
        )
    }
    return moods.get(activo)

@tasks.loop(time=datetime.time(hour=6, minute=35))
async def publish_estacionalidad():
    await bot.wait_until_ready()
    canales = {
        "eurusd": bot.get_channel(EURUSD_CHANNEL_ID),
        "xauusd": bot.get_channel(XAUUSD_CHANNEL_ID),
        "dxy": bot.get_channel(DXY_CHANNEL_ID)
    }
    for activo, canal in canales.items():
        if canal:
            mensaje = f"{generar_estacionalidad(activo)}\n\n{generar_mood(activo)}\n\n📰 Fuente: Forecaster.biz"
            await canal.send(mensaje)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower().strip()

    if content.startswith("!estacionalidad") or content.startswith("estacionalidad"):
        _, _, activo = content.partition(" ")
        activo = activo.strip()

        if activo in ["eurusd", "xauusd", "dxy"]:
            estacionalidad = generar_estacionalidad(activo)
            mood = generar_mood(activo)

            if estacionalidad and mood:
                mensaje = f"{estacionalidad}\n\n{mood}\n\n📰 Fuente: Forecaster.biz"
                await message.channel.send(mensaje)
            else:
                await message.channel.send("❌ Lo siento, no tengo datos para ese activo.")
        else:
            await message.channel.send("❌ Lo siento, no tengo estacionalidad disponible para ese activo.")
    else:
        await bot.process_commands(message)

# === COMANDOS DE SUSCRIPCIÓN ===
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

# === INICIO Y FLASK ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    if not publish_estacionalidad.is_running():
        publish_estacionalidad.start()

def run_bot():
    if not TOKEN:
        print("❗ ERROR: DISCORD_TOKEN no definido")
    else:
        bot.run(TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_bot, name="DiscordBotThread").start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    if content.startswith("!estacionalidad eurusd"):
        resumen = get_forecaster_analysis("eurusd")
        if resumen:
            await message.channel.send(resumen)
    elif content.startswith("!estacionalidad dxy"):
        resumen = get_forecaster_analysis("dxy")
        if resumen:
            await message.channel.send(resumen)
    elif content.startswith("!estacionalidad xauusd"):
        resumen = get_forecaster_analysis("xauusd")
        if resumen:
            await message.channel.send(resumen)

    # Procesa comandos normales también
    await bot.process_commands(message)

import threading
import time
import requests

def ping_self():
    while True:
        try:
            requests.get("https://discord-forex-news-bot.onrender.com")
        except Exception as e:
            print(f"Error en ping: {e}")
        time.sleep(300)  # 5 minutos

ping_thread = threading.Thread(target=ping_self)
ping_thread.start()
