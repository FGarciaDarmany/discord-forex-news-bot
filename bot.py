import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import os

# === TOKEN ===
TOKEN = os.getenv("DISCORD_TOKEN")

# === INTENTS ===
intents = discord.Intents.default()
intents.message_content = True

# === BOT ===
bot = commands.Bot(command_prefix="!", intents=intents)

# === FUNCION SCRAP FORECASTER OB/OS ===
def scrap_obos_forecaster(par="eurusd"):
    try:
        base_url = f"https://terminal.forecaster.biz/instrument/forex/{par}/obos"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        estado = soup.find("div", class_="instrument-score__description")
        estado_texto = estado.text.strip() if estado else "Estado desconocido"

        data_items = soup.find_all("div", class_="score-box__value")
        valores = [item.text.strip() for item in data_items]

        resumen = (
            f"🔵 **Forecaster.biz – {par.upper()} OB/OS**\n"
            f"Estado: {estado_texto}\n"
        )

        if valores:
            resumen += f"▪️ Indicadores: {', '.join(valores)}\n"

        resumen += f"🔗 {base_url}"
        return resumen

    except Exception as e:
        return f"❌ Error al obtener OB/OS: {e}"

# === COMANDO OBOS ===
@bot.command()
async def obos(ctx, par: str = "eurusd"):
    resultado = scrap_obos_forecaster(par)
    await ctx.send(resultado)

# === EVENTO ON_READY ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# === INICIAR BOT ===
if __name__ == "__main__":
    bot.run(TOKEN)
