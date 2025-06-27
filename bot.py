import discord
from discord.ext import commands
import asyncio
import json
import os

# === CONFIGURACIÓN DE INTENTS ===
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # 🔑 NECESARIO para leer comandos

bot = commands.Bot(command_prefix="!", intents=intents)

# === IDS ACTUALIZADOS ===
PROMOCIONAL_ROLE_ID = 1388289561310003200   # Rol Promocional
VISITANTE_ROLE_ID = 1388289303062253568     # Rol Visitante
PREMIUM_ROLE_ID = 1388288386242183208       # Rol Premium

# No tienes canal de logs por ahora
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
    await asyncio.sleep(172800)  # 2 días en segundos
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
@commands.has_permissions(administrator=True)
async def registrar_pago(ctx, member: discord.Member):
    guardar_pagado(member.id)
    premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
    await member.add_roles(premium_role)
    await ctx.send(f"✅ {member.display_name} marcado como **Premium** y agregado a la lista de pagados.")

# === COMANDO: ELIMINAR PAGO ===
@bot.command()
@commands.has_permissions(administrator=True)
async def eliminar_pago(ctx, member: discord.Member):
    eliminar_pagado(member.id)
    premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
    if premium_role in member.roles:
        await member.remove_roles(premium_role)
    await ctx.send(f"❌ {member.display_name} eliminado de la lista de pagados y rol Premium quitado.")

# === COMANDO: ESTADO DE PAGOS ===
@bot.command()
@commands.has_permissions(administrator=True)
async def estado_pagos(ctx):
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

# === READY ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
