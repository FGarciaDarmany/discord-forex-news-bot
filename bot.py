import discord
from discord.ext import commands
import os
import requests
from bs4 import BeautifulSoup
import datetime

# === CONFIGURACIÓN ===
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# === FUNCIONES ===

def obtener_eventos_investing(dia: str = "hoy"):
    try:
        url = "https://es.investing.com/economic-calendar/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        tabla = soup.find("table", {"id": "economicCalendarData"})
        if not tabla:
            return ["❌ No se encontró el calendario de Investing."]
        
        filas = tabla.find_all("tr", class_="js-event-item")
        eventos_alto_impacto = []

        for fila in filas:
            impacto = fila.find("td", class_="sentiment")
            estrellas = impacto.find_all("i", class_="grayFullBullishIcon") if impacto else []

            if len(estrellas) == 3:  # Solo eventos de 3 estrellas
                hora = fila.get("data-event-datetime")
                nombre = fila.find("td", class_="event")
                pais = fila.find("td", class_="flagCur")
                if hora and nombre and pais:
                    eventos_alto_impacto.append(f"🕒 {hora} | 🌎 {pais.text.strip()} | 📌 {nombre.text.strip()}")

        return eventos_alto_impacto if eventos_alto_impacto else ["✅ No hay eventos de alto impacto hoy."]
    
    except Exception as e:
        return [f"❌ Error al obtener eventos de Investing: {e}"]

def obtener_rango_semanal():
    hoy = datetime.date.today()
    inicio = hoy
    fin = hoy + datetime.timedelta(days=6)
    return f"📆 Del {inicio.strftime('%A %d de %B de %Y')} al {fin.strftime('%A %d de %B de %Y')}"

# === COMANDOS ===

@bot.command()
async def calendario(ctx, tipo: str = "hoy"):
    user = ctx.author
    if tipo == "hoy":
        eventos = obtener_eventos_investing("hoy")
        msg = "**📰 Noticias económicas del día (alto impacto - Investing):**\n" + "\n".join(eventos)
        await user.send(msg)
        await ctx.send(f"📩 Calendario enviado por DM, {user.mention}")

    elif tipo == "semanal":
        rango = obtener_rango_semanal()
        url = "https://es.investing.com/economic-calendar/"
        msg = f"**🗓️ Calendario semanal (alto impacto - Investing):**\n{rango}\n🔗 {url}"
        await user.send(msg)
        await ctx.send(f"📩 Calendario semanal enviado por DM, {user.mention}")

    else:
        await ctx.send("❌ Usa: `!calendario hoy` o `!calendario semanal`")

# === EJECUCIÓN ===
if __name__ == "__main__":
    bot.run(TOKEN)
