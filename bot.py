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

# === SCRAPING FUNCIONES (placeholder) ===

def get_ff_news():
    return []  # Aquí iría el scraping real si se desea

# === EVENTOS Y TAREAS ===

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    if not publish_eurusd_forecast.is_running():
        publish_eurusd_forecast.start()
    if not publish_dxy_forecast.is_running():
        publish_dxy_forecast.start()
    if not publish_xauusd_forecast.is_running():
        publish_xauusd_forecast.start()

@tasks.loop(time=datetime.time(hour=6, minute=30))
async def publish_eurusd_forecast():
    await bot.wait_until_ready()
    canal = bot.get_channel(EURUSD_CHANNEL_ID)
    if canal:
        mensaje = (
            "📊 **Resumen Diario EUR/USD – Forecaster AI**\n"
            "🔹 Último cierre: **1.1726** (+0.58%)\n"
            "📈 Tendencia positiva reciente, con fuerte interés comprador por encima de 1.1700.\n\n"
            "🧠 **Análisis Destacado:**\n"
            "💵 USD debilitado por tensiones geopolíticas y expectativas sobre la Fed.\n"
            "🌍 Cese al fuego entre Israel e Irán impulsa el apetito por riesgo.\n"
            "📉 Se espera caída del índice USD de -5.7%\n"
            "📊 EUR/USD podría ir rumbo a **1.20** si se mantiene el impulso.\n\n"
            "🔍 **Conclusión:**\n"
            "Se mantiene un **sesgo alcista** para el Euro. Sostenerse sobre la resistencia es clave.\n\n"
            "📰 Fuente: Forecaster.biz"
        )
        await canal.send(mensaje)

@tasks.loop(time=datetime.time(hour=6, minute=30))
async def publish_dxy_forecast():
    await bot.wait_until_ready()
    canal = bot.get_channel(DXY_CHANNEL_ID)
    if canal:
        mensaje = (
            "📊 **Resumen Diario DXY – Forecaster AI**\n"
            "🔹 Último cierre: **105.23** (-0.34%)\n"
            "📉 El dólar retrocede levemente tras una semana de alta volatilidad.\n\n"
            "🧠 **Factores Relevantes:**\n"
            "📰 Cese de tensiones geopolíticas reduce la demanda de USD como refugio.\n"
            "📊 Expectativas de recorte de tasas en EE.UU. debilitan al índice.\n"
            "💹 Se mantiene soporte en la zona de 104.80, con riesgo de ruptura.\n\n"
            "🔍 **Conclusión:**\n"
            "El DXY presenta presión bajista a corto plazo. Clave: mantener 104.80.\n\n"
            "📰 Fuente: Forecaster.biz"
        )
        await canal.send(mensaje)

@tasks.loop(time=datetime.time(hour=6, minute=30))
async def publish_xauusd_forecast():
    await bot.wait_until_ready()
    canal = bot.get_channel(XAUUSD_CHANNEL_ID)
    if canal:
        mensaje = (
            "📊 **Resumen Diario XAU/USD – Forecaster AI**\n"
            "🔹 Último cierre: **2326.47 USD/oz** (+0.78%)\n"
            "🥇 El oro extiende ganancias respaldado por debilidad del dólar.\n\n"
            "🧠 **Factores Clave:**\n"
            "🌍 Tensiones globales siguen generando demanda de activos refugio.\n"
            "💵 Baja en el DXY favorece flujos hacia commodities.\n"
            "📈 Superó resistencia técnica de 2300, apuntando a zona de 2350-2375.\n\n"
            "🔍 **Conclusión:**\n"
            "El oro muestra momentum alcista sólido. Vigilar pullbacks hacia 2300.\n\n"
            "📰 Fuente: Forecaster.biz"
        )
        await canal.send(mensaje)

# === RESPUESTA POR DM ===
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        activo = message.content.strip().lower()
        respuesta = generar_respuesta_forecaster(activo)
        if respuesta:
            await message.channel.send(respuesta)
        else:
            await message.channel.send(f"❌ Lo siento, no tengo análisis disponible para **{activo.upper()}**.")
    else:
        await bot.process_commands(message)

def generar_respuesta_forecaster(activo):
    resumenes = {
        "audusd": (
            "📊 **AUD/USD – Análisis Forecaster AI**\n"
            "🔹 Último cierre: **0.6753** (+0.21%)\n\n"
            "🧠 El AUD sube moderadamente impulsado por mejoras en commodities.\n"
            "🇦🇺 Australia muestra datos sólidos de empleo y crecimiento.\n"
            "📉 USD débil por expectativas de recorte de tasas.\n\n"
            "🔍 Zona clave de soporte: **0.6670**\n"
            "🔍 Objetivo potencial: **0.6850** si mantiene momentum alcista.\n\n"
            "📰 Fuente: Forecaster.biz"
        ),
        "xauusd": (
            "📊 **XAU/USD – Análisis Forecaster AI**\n"
            "🔹 Último cierre: **2326.47** (+0.78%)\n\n"
            "🥇 El oro gana tracción como refugio ante incertidumbre global.\n"
            "💵 Baja del DXY favorece el impulso del oro.\n"
            "📈 Superó los 2300 USD, apuntando a resistencia de 2350-2375.\n\n"
            "🔍 Soporte clave: **2300**\n"
            "🔍 Potencial objetivo: **2375**\n\n"
            "📰 Fuente: Forecaster.biz"
        ),
        "nas100": (
            "📊 **NASDAQ 100 – Análisis Forecaster AI**\n"
            "🔹 Último cierre: **15,230.45** (+0.95%)\n\n"
            "🧠 Impulso alcista por resultados tecnológicos positivos.\n"
            "💻 Apple, Nvidia y Microsoft impulsan el índice.\n"
            "💵 Contexto de tasas bajas sigue favoreciendo la tecnología.\n\n"
            "🔍 Soporte: **14,900**\n"
            "🔍 Objetivo: **15,600-15,800** si continúa el rally.\n\n"
            "📰 Fuente: Forecaster.biz"
        ),
        "eurusd": (
            "📊 **EUR/USD – Análisis Forecaster AI**\n"
            "🔹 Último cierre: **1.1726** (+0.58%)\n\n"
            "💶 El euro sigue fortaleciéndose frente a un dólar débil.\n"
            "🌍 Menor riesgo geopolítico y expectativas dovish en la Fed.\n"
            "📈 Superó 1.1700 con fuerza, posibles extensiones hacia 1.20.\n\n"
            "🔍 Soporte técnico: **1.1650**\n"
            "🔍 Objetivo: **1.2000**\n\n"
            "📰 Fuente: Forecaster.biz"
        )
    }
    return resumenes.get(activo)

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

# === EJECUCIÓN ===
def run_bot():
    if not TOKEN:
        print("❗ ERROR: DISCORD_TOKEN no definido")
    else:
        bot.run(TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_bot, name="DiscordBotThread").start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
