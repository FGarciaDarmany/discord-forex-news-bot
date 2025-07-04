import discord
from discord.ext import commands
import asyncio
import os
import json
import requests
from bs4 import BeautifulSoup
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


# === COMANDO: ASIGNAR PREMIUM ===
@bot.command(name="premium")
async def asignar_premium(ctx, *members: discord.Member):
    if not (ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator):
        await ctx.send("🚫 No tienes permisos para usar este comando.")
        return

    premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
    free_role = ctx.guild.get_role(FREE_ROLE_ID)
    processed = []

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

        processed.append(member.display_name)

    guardar_lista_premium(ctx.guild)
    guardar_lista_free(ctx.guild)

    if processed:
        await ctx.send(f"✅ Roles **Premium** asignados a: {', '.join(processed)}")
    else:
        await ctx.send("⚠️ No se encontró ningún miembro válido.")


# === COMANDO: REMOVER PREMIUM (PASAR A FREE) ===
@bot.command(name="free")
async def asignar_free(ctx, *members: discord.Member):
    if not (ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator):
        await ctx.send("🚫 No tienes permisos para usar este comando.")
        return

    premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
    free_role = ctx.guild.get_role(FREE_ROLE_ID)
    processed = []

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

        processed.append(member.display_name)

    guardar_lista_premium(ctx.guild)
    guardar_lista_free(ctx.guild)

    if processed:
        await ctx.send(f"❌ Roles **Premium** removidos y asignados como **Free**: {', '.join(processed)}")
    else:
        await ctx.send("⚠️ No se encontró ningún miembro válido.")


# === CONSULTA DE SPREAD Y CALENDARIO VIA DM ===
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if isinstance(message.channel, discord.DMChannel):
        guild = bot.guilds[0]
        member = guild.get_member(message.author.id) or await guild.fetch_member(message.author.id)
        if not member:
            await message.channel.send("⚠️ No pude verificar tus roles.")
            return

        is_admin = member.guild_permissions.administrator
        premium_role = guild.get_role(PREMIUM_ROLE_ID)
        if not is_admin and premium_role not in member.roles:
            await message.channel.send(
                "🚫 Eres usuario Free. No tienes permiso para usar consultas.\n"
                "Actualiza a Premium para desbloquear esta funcionalidad. 💎"
            )
            return

        content = message.content.lower().strip()

        if content == "calendario hoy" or content == "calendario semana":
            await message.channel.send("📡 Consultando calendario económico...")

            eventos = await obtener_calendario_economico(content)

            if not eventos:
                await message.channel.send("⚠️ No se encontraron noticias de alto impacto.")
                return

            embed = discord.Embed(
                title=f"📅 Calendario Económico - {'Hoy' if 'hoy' in content else 'Semana'}",
                description="Noticias de alto impacto",
                color=0x00ff00
            )

            for evento in eventos:
                embed.add_field(
                    name=f"{evento['hora']} | {evento['país']} | {evento['evento']}",
                    value=f"Impacto: {evento['impacto']}\n"
                          f"Actual: {evento['actual']}\n"
                          f"Previsión: {evento['previsto']}\n"
                          f"Anterior: {evento['anterior']}",
                    inline=False
                )

            await message.channel.send(embed=embed)
            return

        # Si no es calendario => Spread
        # (Puedes mantener tu lógica de spread aquí si quieres.)

    else:
        await bot.process_commands(message)


# === SCRAPING DEL CALENDARIO ECONÓMICO ===
async def obtener_calendario_economico(tipo):
    eventos = []

    url = "https://www.forexfactory.com/calendar.php"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    filas = soup.find_all("tr", class_="calendar__row")
    for fila in filas:
        impacto = fila.find("td", class_="impact").get("title", "")
        if "High Impact Expected" in impacto:
            hora = fila.find("td", class_="time").text.strip()
            país = fila.find("td", class_="flag").get("title", "")
            evento = fila.find("td", class_="event").text.strip()
            actual = fila.find("td", class_="actual").text.strip()
            previsto = fila.find("td", class_="forecast").text.strip()
            anterior = fila.find("td", class_="previous").text.strip()

            eventos.append({
                "hora": hora,
                "país": país,
                "evento": evento,
                "impacto": "Alto",
                "actual": actual,
                "previsto": previsto,
                "anterior": anterior
            })

    return eventos


# === BOT READY ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
