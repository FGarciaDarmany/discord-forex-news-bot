import discord
from discord.ext import commands
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# === FUNCIONES DE CALENDARIO ===
def obtener_eventos_alto_impacto():
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
        for fila in filas:
            estrellas = fila.find("td", class_="sentiment")
            if estrellas and estrellas.text.count("★") >= 3:
                hora = fila.get("data-event-datetime")
                nombre = fila.find("td", class_="event")
                pais_td = fila.find("td", class_="flagCur")
                pais = pais_td.text.strip() if pais_td else ""
                impacto = "🔴 Alto impacto"
                if hora and nombre and pais:
                    eventos.append(f"⏰ {hora} | 🌍 {pais} | 📌 {nombre.text.strip()} | {impacto}")
        return eventos if eventos else ["✅ No hay eventos de alto impacto hoy"]
    except Exception as e:
        return [f"❌ Error al obtener eventos: {e}"]

# === COMANDOS ===
@bot.command()
async def calendario(ctx, tipo: str = "hoy"):
    if tipo == "hoy":
        eventos = obtener_eventos_alto_impacto()
        user = ctx.author
        await user.send("📬 **Noticias económicas del día (alto impacto):**")
        for evento in eventos:
            await user.send(evento)
        await ctx.send(f"📨 Calendario enviado por DM, {user.mention}")

    elif tipo == "semanal":
        await ctx.author.send("📅 **Calendario semanal (Investing):**\nhttps://es.investing.com/economic-calendar/")
        await ctx.send(f"📨 Calendario semanal enviado por DM, {ctx.author.mention}")

    else:
        await ctx.send("❌ Usa: `!calendario hoy` o `!calendario semanal`")

if __name__ == "__main__":
    bot.run(TOKEN)
