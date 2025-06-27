import discord
from discord.ext import commands, tasks
import os
import requests
import datetime
from bs4 import BeautifulSoup

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# === FUNCIONES DE CALENDARIO ===
def obtener_eventos_investing():
    try:
        url = "https://es.investing.com/economic-calendar/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        tabla = soup.find("table", {"id": "economicCalendarData"})
        if not tabla:
            return ["❌ No se encontró el calendario."]

        filas = tabla.find_all("tr", class_="js-event-item")
        eventos = []
        for fila in filas[:10]:
            hora = fila.get("data-event-datetime")
            impacto = fila.find("td", class_="sentiment")
            impacto_emoji = impacto.get("title", "") if impacto else ""
            nombre = fila.find("td", class_="event")
            pais = fila.find("td", class_="flagCur")
            if hora and nombre and pais:
                eventos.append(f"🕒 {hora} | 🌎 {pais.text.strip()} | 📌 {nombre.text.strip()} | {impacto_emoji}")
        return eventos if eventos else ["✅ No hay eventos relevantes hoy"]
    except Exception as e:
        return [f"❌ Error al obtener eventos: {e}"]

# === COMANDOS ===
@bot.command()
async def calendario(ctx, tipo: str = "hoy"):
    if tipo == "hoy":
        eventos = obtener_eventos_investing()
        await ctx.send("🗓️ **Noticias económicas del día (Investing):**")
        for evento in eventos:
            await ctx.send(evento)
    elif tipo == "semanal":
        await ctx.send("📆 Calendario semanal (fuente): https://es.investing.com/economic-calendar/")
    else:
        await ctx.send("❌ Usa: `!calendario hoy` o `!calendario semanal`")

# === EJECUCIÓN ===
if __name__ == "__main__":
    bot.run(TOKEN)
