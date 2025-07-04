import discord
from discord.ext import commands
import asyncio
import json
import os
from dotenv import load_dotenv

# === CARGAR VARIABLES DE ENTORNO ===
load_dotenv()

# === CONFIGURACIÓN DE INTENTS ===
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === IDS ACTUALIZADOS ===
PREMIUM_ROLE_ID = 1388288386242183208
FREE_ROLE_ID = 1390752446724444180

# === ARCHIVOS DE USUARIOS ===
USUARIOS_PREMIUM_FILE = "usuarios premium.txt"
USUARIOS_FREE_FILE = "usuarios free.txt"

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

    # Mensaje privado de bienvenida
    try:
        await member.send(
            f"👋 ¡Bienvenido {member.display_name}!\n"
            f"Ahora formas parte de nuestra comunidad **Free**.\n"
            f"Podrás acceder a los canales generales.\n"
            f"Para desbloquear herramientas Premium, proyecciones y sesiones en vivo, contáctanos cuando quieras. 🚀"
        )
    except Exception as e:
        print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

# === COMANDO: AGREGAR PREMIUM A VARIOS ===
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

# === COMANDO: REMOVER PREMIUM A VARIOS Y PASAR A FREE (SOLO POR DM) ===
@bot.command(name="-premium")
async def quitar_premium(ctx, *members: discord.Member):
    if ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
        premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
        free_role = ctx.guild.get_role(FREE_ROLE_ID)

        for member in members:
            if premium_role in member.roles:
                await member.remove_roles(premium_role)
            await member.add_roles(free_role)

            # Enviar aviso por DM
            try:
                await member.send(
                    f"👋 ¡Hola {member.display_name}!\n"
                    f"Tu acceso **Premium** ha finalizado y ahora formas parte de los usuarios **Free**.\n"
                    f"⚠️ Ya no tendrás acceso a proyecciones, herramientas de trading ni sesiones en vivo.\n"
                    f"✅ Puedes seguir participando en el canal general y mantenerte conectado con la comunidad. 💪"
                )
            except Exception as e:
                print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

        guardar_lista_premium(ctx.guild)
        guardar_lista_free(ctx.guild)
        menciones = ", ".join([member.display_name for member in members])
        await ctx.send(f"❌ Roles **Premium** removidos y asignados como **Free**: {menciones}")
    else:
        await ctx.send("🚫 No tienes permisos para usar este comando.")

# === READY ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
