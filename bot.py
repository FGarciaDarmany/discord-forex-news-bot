from scraper import obtener_pronostico, obtener_estacionalidad, obtener_obos
@bot.command()
async def pronostico(ctx, activo: str):
    guild = ctx.guild
    member = guild.get_member(ctx.author.id)
    premium_role = guild.get_role(PREMIUM_ROLE_ID)

    if premium_role not in member.roles:
        await ctx.send("🚫 Solo usuarios Premium pueden usar este comando.")
        return

    await ctx.send(f"📡 Consultando pronóstico para **{activo.upper()}**...")

    texto = await obtener_pronostico(activo.upper(), os.getenv("FORECAST_USER"), os.getenv("FORECAST_PASS"))
    await ctx.send(f"**Pronóstico {activo.upper()}**\n```{texto.strip()}```")

@bot.command()
async def estacionalidad(ctx, activo: str):
    guild = ctx.guild
    member = guild.get_member(ctx.author.id)
    premium_role = guild.get_role(PREMIUM_ROLE_ID)

    if premium_role not in member.roles:
        await ctx.send("🚫 Solo usuarios Premium pueden usar este comando.")
        return

    await ctx.send(f"📊 Generando informe de estacionalidad para **{activo.upper()}**...")

    buffer = await obtener_estacionalidad(activo.upper(), os.getenv("FORECAST_USER"), os.getenv("FORECAST_PASS"))
    await ctx.send(file=discord.File(fp=buffer, filename=f"estacionalidad_{activo.upper()}.png"))

@bot.command()
async def obos(ctx, activo: str):
    guild = ctx.guild
    member = guild.get_member(ctx.author.id)
    premium_role = guild.get_role(PREMIUM_ROLE_ID)

    if premium_role not in member.roles:
        await ctx.send("🚫 Solo usuarios Premium pueden usar este comando.")
        return

    await ctx.send(f"📈 Consultando nivel Overbought/Oversold para **{activo.upper()}**...")

    buffer = await obtener_obos(activo.upper(), os.getenv("FORECAST_USER"), os.getenv("FORECAST_PASS"))
    await ctx.send(file=discord.File(fp=buffer, filename=f"obos_{activo.upper()}.png"))
