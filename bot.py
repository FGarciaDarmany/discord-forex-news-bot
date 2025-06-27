import discord
from discord.ext import commands
import os
import datetime
import json

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === Simulación de calendario de Investing ===
def obtener_calendario_hoy():
    eventos_hoy = [
        {"hora": "08:30", "impacto": "🔴", "evento": "Nóminas no agrícolas (USD)"},
        {"hora": "10:00", "impacto": "🟢", "evento": "Inventarios de petróleo crudo (USD)"},
        {"hora": "14:00", "impacto": "🔴", "evento": "Decisión de tipos del FOMC (USD)"},
        {"hora": "15:30", "impacto": "🕠", "evento": "Discurso de Lagarde (EUR)"},
    ]
    return "\n".join([f"{e['impacto']} `{e['hora']}` {e['evento']}" for e in eventos_hoy])

def obtener_calendario_semanal():
    eventos_semanales = {
        "Friday 27/06": [
            {"hora": "08:00", "impacto": "🕠", "evento": "PIB Trimestral (GBP)"},
            {"hora": "09:00", "impacto": "🔴", "evento": "IPC Anual (EUR)"},
            {"hora": "10:30", "impacto": "🟢", "evento": "Peticiones de Subsidio (USD)"},
        ],
        "Saturday 28/06": [
            {"hora": "08:30", "impacto": "🔴", "evento": "Empleo ADP (USD)"},
            {"hora": "11:00", "impacto": "🕠", "evento": "Inventarios de crudo (USD)"},
        ]
    }
    salida = ""
    for dia, eventos in eventos_semanales.items():
        salida += f"\n📅 **{dia}**\n"
        for e in eventos:
            salida += f"{e['impacto']} `{e['hora']}` {e['evento']}\n"
    return salida.strip()

@bot.command()
async def calendario(ctx, tipo: str = None):
    if tipo == "hoy":
        await ctx.send("📅 **Noticias económicas del día:**\n🔗 https://www.forexfactory.com/calendar")
    elif tipo == "semanal":
        await ctx.send("📅 **Calendario semanal:**\n🔗 https://www.investing.com/economic-calendar/")
    else:
        await ctx.send("❌ Usa: `!calendario hoy` o `!calendario semanal`")

        await ctx.send(mensaje)
    else:
        await ctx.send("❌ Usa el comando así: `!calendario hoy` o `!calendario semanal`")

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

if __name__ == "__main__":
    if not TOKEN:
        print("❗ ERROR: DISCORD_TOKEN no definido")
    else:
        bot.run(TOKEN)
