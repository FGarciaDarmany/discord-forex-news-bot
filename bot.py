import discord
from discord.ext import commands
import asyncio
import json
import os
import requests
from dotenv import load_dotenv

# === CARGAR VARIABLES DE ENTORNO ===
load_dotenv()

# === CONFIGURACIÓN DE INTENTS ===
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Necesario para leer comandos y DMs

bot = commands.Bot(command_prefix="!", intents=intents)

# === IDS ACTUALIZADOS ===
PROMOCIONAL_ROLE_ID = 1388289561310003200
VISITANTE_ROLE_ID = 1388289303062253568
PREMIUM_ROLE_ID = 1388288386242183208

LOG_CHANNEL_ID = None

# === ARCHIVO DE PAGOS ===
PAGOS_FILE = "pagos.json"

# === FUNCIONES PARA GESTIONAR PAGOS ===
def cargar_pagados():
    if not os.path.exists(PAGOS_FILE):
        return []
    with open(PAGOS_FILE, "r") as f:
        data = json.load(f)
    return data.get("usuarios_pagados", [])

def guardar_pagado(user_id):
    pagados = cargar_pagados()
    if user_id not in pagados:
        pagados.append(user_id)
        with open(PAGOS_FILE, "w") as f:
            json.dump({"usuarios_pagados": pagados}, f, indent=4)

def eliminar_pagado(user_id):
    pagados = cargar_pagados()
    if user_id in pagados:
        pagados.remove(user_id)
        with open(PAGOS_FILE, "w") as f:
            json.dump({"usuarios_pagados": pagados}, f, indent=4)

# === DETECTAR CUANDO ASIGNAS PROMOCIONAL ===
@bot.event
async def on_member_update(before, after):
    promocional_role = after.guild.get_role(PROMOCIONAL_ROLE_ID)
    if promocional_role in after.roles and promocional_role not in before.roles:
        await esperar_y_cambiar(after)

# === LÓGICA: ESPERAR 2 DÍAS Y CAMBIAR ROL ===
async def esperar_y_cambiar(member):
    await asyncio.sleep(172800)
    pagados = cargar_pagados()
    guild = member.guild
    promocional_role = guild.get_role(PROMOCIONAL_ROLE_ID)
    visitante_role = guild.get_role(VISITANTE_ROLE_ID)
    premium_role = guild.get_role(PREMIUM_ROLE_ID)
    log_channel = guild.get_channel(LOG_CHANNEL_ID) if LOG_CHANNEL_ID else None

    if (
        promocional_role in member.roles
        and premium_role not in member.roles
        and member.id not in pagados
    ):
        await member.remove_roles(promocional_role)
        await member.add_roles(visitante_role)
        try:
            await member.send(
                "⏰ Tu acceso **Promocional** terminó.\n"
                "Ahora eres **Visitante**.\n"
                "💡 Para acceder a servicios **Premium**, abona tu cuota cuando quieras. 🚀"
            )
        except:
            print(f"No se pudo enviar DM a {member.name}")

        if log_channel:
            await log_channel.send(
                f"✅ {member.mention} pasó de Promocional ➜ Visitante (sin pago registrado)."
            )

# === COMANDO: REGISTRAR PAGO ===
@bot.command()
async def registrar_pago(ctx, member: discord.Member):
    if ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
        guardar_pagado(member.id)
        premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
        await member.add_roles(premium_role)
        await ctx.send(f"✅ {member.display_name} marcado como **Premium** y agregado a la lista de pagados.")
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === COMANDO: ELIMINAR PAGO ===
@bot.command()
async def eliminar_pago(ctx, member: discord.Member):
    if ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
        eliminar_pagado(member.id)
        premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
        if premium_role in member.roles:
            await member.remove_roles(premium_role)
        await ctx.send(f"❌ {member.display_name} eliminado de la lista de pagados y rol Premium quitado.")
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === COMANDO: ESTADO DE PAGOS ===
@bot.command()
async def estado_pagos(ctx):
    if ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
        guild = ctx.guild
        pagados = cargar_pagados()
        premium_role = guild.get_role(PREMIUM_ROLE_ID)
        promocional_role = guild.get_role(PROMOCIONAL_ROLE_ID)
        visitante_role = guild.get_role(VISITANTE_ROLE_ID)

        miembros_pagados = []
        miembros_no_pagados = []

        for member in guild.members:
            if member.bot:
                continue
            if member.id in pagados or premium_role in member.roles:
                miembros_pagados.append(f"{member.display_name} ({member.id})")
            elif promocional_role in member.roles or visitante_role in member.roles:
                miembros_no_pagados.append(f"{member.display_name} ({member.id})")

        embed = discord.Embed(
            title="📊 Estado de Pagos",
            description="Usuarios Pagados y Pendientes",
            color=0x00FF00
        )
        embed.add_field(
            name="✅ PAGADOS",
            value="\n".join(miembros_pagados) if miembros_pagados else "Ninguno",
            inline=False
        )
        embed.add_field(
            name="❌ NO PAGADOS",
            value="\n".join(miembros_no_pagados) if miembros_no_pagados else "Ninguno",
            inline=False
        )

        await ctx.send(embed=embed)
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === NUEVO: CONSULTAR SPREAD POR DM ===

optimal_spreads = {
    "EURUSD": 1.0,
    "XAUUSD": 20.0
}

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        pair = message.content.strip().upper()

        if pair not in optimal_spreads:
            await message.channel.send(
                f"❌ Par '{pair}' no soportado.\nPares disponibles: {', '.join(optimal_spreads.keys())}"
            )
            return

        await message.channel.send(f"🔍 Consultando spread de {pair}...")

        API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not API_KEY:
            await message.channel.send("❌ No se encontró la API Key. Verifica tu configuración.")
            return

        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={pair[:3]}&to_currency={pair[3:]}&apikey={API_KEY}"

        try:
            response = requests.get(url)
            data = response.json()

            if "Realtime Currency Exchange Rate" not in data:
                await message.channel.send(
                    f"⚠️ Respuesta inesperada de la API:\n```{json.dumps(data, indent=2)}```"
                )
                return

            bid = float(data["Realtime Currency Exchange Rate"]["8. Bid Price"])
            ask = float(data["Realtime Currency Exchange Rate"]["9. Ask Price"])

            spread = (ask - bid) * 10000 if pair != "XAUUSD" else (ask - bid) * 100

            optimal = "ÓPTIMO ✅" if spread <= optimal_spreads[pair] else "NO ÓPTIMO 🚫"

            await message.channel.send(
                f"🔍 **Informe de Spread {pair}**\n"
                f"📉 **BID:** {bid}\n"
                f"📈 **ASK:** {ask}\n"
                f"📊 **Spread:** {spread:.2f} pips\n"
                f"📌 **Estado:** {optimal}"
            )

        except Exception as e:
            await message.channel.send(f"⚠️ Error al consultar el spread:\n```{e}```")

    await bot.process_commands(message)

# === READY ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
