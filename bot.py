import discord
from discord.ext import commands
import asyncio
import json
import os
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

# === PARES Y SPREADS ÓPTIMOS ===
optimal_spreads = {
    "GBPCHF": 2.0,
    "GBPUSD": 1.5,
    "AUDUSD": 1.5,
    "EURUSD": 1.0,
    "USDCAD": 1.5,
    "US30": 15.0,
    "USDCHF": 1.5,
    "SPX500": 10.0,
    "EURGBP": 1.5,
    "NZDUSD": 1.5,
    "USDJPY": 1.5,
    "EURJPY": 1.5,
}

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
            f"Podrás acceder a los canales generales.\n"
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
        guardar_lista_premium(ctx.guild)
        guardar_lista_free(ctx.guild)
        menciones = ", ".join([member.display_name for member in members])
        await ctx.send(f"✅ Roles **Premium** asignados a: {menciones}")
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === COMANDO: QUITAR PREMIUM ===
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
                    f"👋 Hola {member.display_name}, ahora formas parte de los usuarios **Free**.\n"
                    f"⚠️ Como Free no tendrás acceso a servicios Premium como proyecciones, herramientas de trading ni sesiones en vivo.\n"
                    f"✅ Pero podrás seguir participando en nuestro canal general y mantenerte conectado con la comunidad. 💪"
                )
            except Exception as e:
                print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

        guardar_lista_premium(ctx.guild)
        guardar_lista_free(ctx.guild)
        menciones = ", ".join([member.display_name for member in members])
        await ctx.send(f"❌ Roles **Premium** removidos y asignados como **Free**: {menciones}")
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === CONSULTAR SPREAD POR DM ===
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        pair = message.content.strip().upper()

        member = None
        for guild in bot.guilds:
            possible_member = guild.get_member(message.author.id)
            if possible_member:
                member = possible_member
                break

        if not member:
            await message.channel.send("⚠️ No se pudo verificar tu rol. Intenta más tarde o avisa a un admin.")
            return

        premium_role = member.guild.get_role(PREMIUM_ROLE_ID)
        if not (premium_role in member.roles or member.guild_permissions.administrator):
            await message.channel.send(
                "🚫 Eres usuario **Free** y no tienes acceso a consultas de spread.\n"
                "💡 Para desbloquear esta función, solicita acceso **Premium**. 🚀"
            )
            return

        if pair not in optimal_spreads:
            await message.channel.send(
                f"❌ Par '{pair}' no soportado.\nPares disponibles: {', '.join(optimal_spreads.keys())}"
            )
            return

        await message.channel.send(f"🔍 Consultando spread de {pair} (Twelve Data)...")

        API_KEY = TWELVE_DATA_API_KEY
        print(f"🔑 API Key en uso: {API_KEY}")

        symbol = f"{pair[:3]}/{pair[3:]}"
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}"

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

            spread = (ask - bid) * 10000
            optimal = "ÓPTIMO ✅" if spread <= optimal_spreads[pair] else "NO ÓPTIMO 🚫"

            await message.channel.send(
                f"🔍 **Informe de Spread {pair}**\n"
                f"📉 **BID/LOW:** {bid}\n"
                f"📈 **ASK/HIGH:** {ask}\n"
                f"🔢 **Método:** {metodo}\n"
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
