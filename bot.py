import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
from flask import Flask
import threading
import time
import urllib.parse

# === CONFIGURACIÓN GENERAL ===
TOKEN = os.getenv("DISCORD_TOKEN")
EURUSD_CHANNEL_ID = 1387745037944881193
DXY_CHANNEL_ID = 1387745143993401495
XAUUSD_CHANNEL_ID = 1387745575734218782
SUBSCRIBERS_FILE = "subscribers.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === FLASK KEEP-ALIVE ===
app = Flask(__name__)
@app.route('/')
def home():
    return "✅ Bot en línea y funcionando correctamente."

# === MANEJO DE SUBSCRIPTORES POR DM ===
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

# === FUNCIONES DE CONTENIDO ===
def generar_estacionalidad(activo):
    estacionales = {
        "eurusd": "📆 **Estacionalidad de JUNIO – EUR/USD**...",
        "xauusd": "📆 **Estacionalidad de JUNIO – XAU/USD**...",
        "dxy": "📆 **Estacionalidad de JUNIO – DXY**..."
    }
    return estacionales.get(activo)

def generar_mood(activo):
    moods = {
        "eurusd": "🔵 **Market Mood EUR/USD**...",
        "xauusd": "🔵 **Market Mood XAU/USD**...",
        "dxy": "🔵 **Market Mood DXY**..."
    }
    return moods.get(activo)

def get_forecaster_analysis(activo):
    try:
        base_url = "https://forecaster.biz"
        search_url = f"{base_url}/search?q={activo}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(r.content, "html.parser")
        link_tag = soup.select_one("div.asset-card a[href*='/analysis/']")
        if not link_tag:
            return "❌ No se encontró análisis para este activo."
        full_url = urllib.parse.urljoin(base_url, link_tag['href'])
        r2 = requests.get(full_url, headers=headers)
        soup2 = BeautifulSoup(r2.content, "html.parser")
        section = soup2.find("div", string="What's Happening")
        if not section:
            return "❌ No se encontró el análisis 'What's Happening'."
        analysis_container = section.find_next("div")
        analysis_text = analysis_container.get_text(separator="\n").strip()
        return f"📘 **Forecaster.biz – What's Happening**\n{analysis_text}"
    except Exception as e:
        return f"❌ Error al obtener el análisis: {e}"

def get_news_today(limit=5):
    try:
        url = "https://www.forexfactory.com/news"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, "html.parser")
        headlines = soup.select("a.title__text")
        news = []
        for h in headlines[:limit]:
            title = h.text.strip()
            link = urllib.parse.urljoin(url, h["href"])
            news.append(f"📰 {title}\n🔗 {link}")
        return news
    except Exception as e:
        return [f"❌ Error al obtener noticias: {e}"]

# === TAREA PROGRAMADA DIARIA ===
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

# === PROCESAR COMANDOS SIN RESPUESTA DOBLE ===
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# === COMANDOS DISPONIBLES ===
@bot.command()
async def estacionalidad(ctx, activo: str = "eurusd"):
    activo = activo.lower()
    if activo in ["eurusd", "xauusd", "dxy"]:
        estacionalidad = generar_estacionalidad(activo)
        mood = generar_mood(activo)
        analisis = get_forecaster_analysis(activo)
        mensaje = f"{estacionalidad}\n\n{mood}\n\n{analisis}\n\n📰 Fuente: Forecaster.biz"
        await ctx.send(mensaje)
    else:
        await ctx.send("❌ Activo no válido. Usa: eurusd, xauusd o dxy.")

@bot.command()
async def analisis(ctx, par: str = "eurusd"):
    resumen = get_forecaster_analysis(par)
    try:
        await ctx.author.send(resumen)
        await ctx.send("📩 Análisis enviado por DM.")
    except:
        await ctx.send("❌ No pude enviarte el DM. Activá los mensajes privados.")

@bot.command()
async def noticias(ctx):
    noticias = get_news_today()
    for noticia in noticias:
        await ctx.author.send(noticia)
    await ctx.send("📬 Noticias enviadas por DM.")

@bot.command()
async def calendario(ctx, tipo: str = None):
    if tipo == "hoy":
        await ctx.send("🗓 **Noticias económicas del día:**\n🔗 https://www.forexfactory.com/calendar")

@bot.command()
async def setup(ctx, tipo: str = None):
    if tipo == "lit":
        mensaje = (
            "🎯 **Setup LIT básico:**\n"
            "1. BOS interno + FVG\n"
            "2. TDI en zona favorable\n"
            "3. Confirmación en 1m\n"
            "💡 Buscar liquidez inducida previa al movimiento"
        )
        await ctx.send(mensaje)

@bot.command()
async def oro(ctx):
    await ctx.send("🥇 **Oro (XAU/USD):**\nSesgo alcista tras rechazo en zona 2300.\nSoporte clave: 2290\nResistencia: 2335")

@bot.command()
async def euro(ctx):
    await ctx.send("💶 **Euro (EUR/USD):**\nMantiene impulso sobre 1.0700.\nPróxima resistencia: 1.0780\nSoporte dinámico: 1.0685")

@bot.command()
async def dxy(ctx):
    await ctx.send("💲 **Dólar Index (DXY):**\nDebilidad persistente por debajo de 105.00\nPróximo soporte: 104.20\nResistencia: 105.10")

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

# === CONEXIÓN DEL BOT ===
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

def ping_self():
    while True:
        try:
            requests.get("https://discord-forex-news-bot.onrender.com")
        except Exception as e:
            print(f"Error en ping: {e}")
        time.sleep(300)

# === EJECUCIÓN FINAL ===
if __name__ == "__main__":
    threading.Thread(target=run_bot, name="DiscordBotThread").start()
    threading.Thread(target=ping_self, name="KeepAliveThread").start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
