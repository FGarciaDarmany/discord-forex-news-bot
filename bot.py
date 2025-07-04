import discord
from discord.ext import commands
import asyncio
import os
import json
import requests
from dotenv import load_dotenv

# === CARGAR VARIABLES DE ENTORNO ===
load_dotenv()

# === CONFIG INTENTS ===
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === IDS ===
PREMIUM_ROLE_ID = 1388288386242183208
FREE_ROLE_ID = 1390752446724444180

# === ARCHIVOS ===
USUARIOS_PREMIUM_FILE = "usuarios premium.txt"
USUARIOS_FREE_FILE = "usuarios free.txt"

# === TWELVE DATA API ===
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

# === FUNCIONES PARA GUARDAR LISTAS ===
def guardar_lista_premium(guild):
    premium_role = guild.get_role(PREMIUM_ROLE_ID)
    if premium_role:
        premium_members = [m.display_name for m in premium_role.members if not m.bot]
        with open(USUARIOS_PREMIUM_FILE, "w", encoding="utf-8") as f:
            for user in premium_members:
                f.write(f"{user}\n")
        print("✅ Lista de usuarios Premium actualizada.")

def guardar_lista_free(guild):
    free_role = guild.get_role(FREE_ROLE_ID)
    if free_role:
        free_members = [m.display_name for m in free_role.members if not m.bot]
        with open(USUARIOS_FREE_FILE, "w", encoding="utf-8") as f:
            for user in free_members:
                f.write(f"{user}\n")
        print("✅ Lista de usuarios Free actualizada.")

# === EVENTO: NUEVO USUARIO ===
@bot.event
async def on_member_join(member):
    guild = member.guild
    free_role = guild.get_role(FREE_ROLE_ID)
    if free_role:
        await member.add_roles(free_role)
        guardar_lista_free(guild)
        print(f"✅ Rol Free asignado a {member.display_name}")

    try:
        await member.send(
            f"👋 ¡Bienvenido {member.display_name}!\n"
            f"Ahora formas parte de nuestra comunidad **Free**.\n"
            f"Accedes solo a los canales generales.\n"
            f"Para desbloquear herramientas Premium, proyecciones y sesiones en vivo, contáctanos cuando quieras. 🚀"
        )
    except Exception as e:
        print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

# === COMANDO: AGREGAR PREMIUM ===
@bot.command(name="+premium")
async def agregar_premium(ctx, *members: discord.Member):
    if ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
        premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
        free_role = ctx.guild.get_role(FREE_ROLE_ID)
        for member in members:
            await member.add_roles(premium_role)
            if free_role in member.roles:
                await member.remove_roles(free_role)
            try:
                await member.send(
                    f"🟥 **Bienvenido a la élite Premium, {member.display_name}!**\n"
                    f"Como diría Morfeo: *“Lo único que te ofrezco es la verdad, nada más.”*\n"
                    f"Tomaste la pastilla roja. Has decidido salir de la Matrix.\n"
                    f"🚀 Gracias por tu confianza, ahora desbloqueas proyecciones, herramientas de trading y sesiones exclusivas.\n"
                    f"¡Prepárate para ver hasta dónde llega la madriguera del conejo! 🐇"
                )
            except Exception as e:
                print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

        guardar_lista_premium(ctx.guild)
        guardar_lista_free(ctx.guild)
        menciones = ", ".join([member.display_name for member in members])
        await ctx.send(f"✅ Roles **Premium** asignados a: {menciones}")
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === COMANDO: REMOVER PREMIUM ===
@bot.command(name="-premium")
async def quitar_premium(ctx, *members: discord.Member):
    if ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
        premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
        free_role = ctx.guild.get_role(FREE_ROLE_ID)

        for member in members:
            if premium_role in member.roles:
                await member.remove_roles(premium_role)
            await member.add_roles(free_role)
            try:
                await member.send(
                    f"👋 {member.display_name}, ahora formas parte de los usuarios **Free**.\n"
                    f"⚠️ Como Free no tendrás acceso a servicios **Premium** como proyecciones, herramientas de trading ni sesiones en vivo.\n"
                    f"✅ Puedes seguir participando en nuestro canal general y mantenerte conectado con la comunidad."
                )
            except Exception as e:
                print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

        guardar_lista_premium(ctx.guild)
        guardar_lista_free(ctx.guild)
        menciones = ", ".join([member.display_name for member in members])
        await ctx.send(f"❌ Roles **Premium** removidos y asignados como **Free**: {menciones}")
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === CONSULTA DE SPREAD VIA DM ===
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if isinstance(message.channel, discord.DMChannel):
        pair = message.content.strip().upper()
        guild = bot.guilds[0]
        member = guild.get_member(message.author.id)
        if not member:
            await message.channel.send("⚠️ No pude verificar tus roles.")
            return

        is_admin = member.guild_permissions.administrator
        premium_role = guild.get_role(PREMIUM_ROLE_ID)
        if not is_admin and premium_role not in member.roles:
            await message.channel.send(
                "🚫 Eres usuario Free. No tienes permiso para usar consultas de spread.\n"
                "Actualiza a Premium para desbloquear esta funcionalidad. 💎"
            )
            return

        pares_disponibles = [
            "GBPCHF", "GBPUSD", "AUDUSD", "EURUSD", "USDCAD",
            "US30", "USDCHF", "SPX500", "EURGBP", "NZDUSD", "USDJPY", "EURJPY"
        ]

        if pair not in pares_disponibles:
            await message.channel.send(
                f"❌ Par '{pair}' no soportado.\n"
                f"Pares disponibles: {', '.join(pares_disponibles)}"
            )
            return

        await message.channel.send(f"🔍 Consultando spread de {pair} (Twelve Data)...")

        symbol = f"{pair[:3]}/{pair[3:]}" if len(pair) == 6 else pair
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TWELVE_DATA_API_KEY}"

        try:
            response = requests.get(url)
            data = response.json()

            if "bid" in data and "ask" in data and data["bid"] and data["ask"]:
                bid = float(data["bid"])
                ask = float(data["ask"])
                metodo = "Fuente directa BID/ASK"
            elif "low" in data and "high" in data:
                bid = float(data["low"])
                ask = float(data["high"])
                metodo = "Estimado usando Low/High"
            else:
                await message.channel.send(
                    f"⚠️ No se pudo calcular el spread con la información recibida:\n```{json.dumps(data, indent=2)}```"
                )
                return

            spread = (ask - bid) * 10000 if "USD" in pair else (ask - bid) * 100
            optimal_spread = 1.0
            estado = "ÓPTIMO ✅" if spread <= optimal_spread else "NO ÓPTIMO 🚫"

            await message.channel.send(
                f"🔍 **Informe de Spread {pair}**\n"
                f"📉 **BID/LOW:** {bid}\n"
                f"📈 **ASK/HIGH:** {ask}\n"
                f"🔢 **Método:** {metodo}\n"
                f"📊 **Spread:** {spread:.2f} pips\n"
                f"📌 **Estado:** {estado}"
            )

        except Exception as e:
            await message.channel.send(f"⚠️ Error al consultar el spread:\n```{e}```")
    else:
        await bot.process_commands(message)

# === BOT READY ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
