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
