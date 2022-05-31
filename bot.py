# TOKEN DEL BOT
TOKEN = ""

# Archivo donde registrara logs (Quien ha usado, o intentado usar el bot, etc.)
LOG_FILE = "logs.txt"

# Archivos que contienen los codigos
CODES_FILE = "plata.txt", "diamante.txt", "oro.txt"

# Role ID
ROLE_ID = 867366769392091157

# Tiempo de espera para volver a usar el bot
COOLDOWN = 60

# imports
import asyncio
import discord
from discord.ext import commands
import random
import aiofiles
import time
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)
gen_role = None
# command_prefix= simbolo para usar el bot
bot = commands.Bot(command_prefix="-", intents=discord.Intents.all(), case_insensitive=True) # prefix here

async def getEmbed(type, arg=None): # change colours if you want to here 
    if type == 0:
        embed = discord.Embed(title="Envia el codigo.", description="Revisa tus DMs.", colour=discord.Colour.green())
        return embed
    elif type == 1:
        embed = discord.Embed(title="Este es el codigo generado.", description=arg, colour=discord.Colour.blue())
        return embed
    elif type == 2:
        embed = discord.Embed(title="Fuera de stock.", description="Los codigos estan fuera de stock.", colour=discord.Colour.red())
        return embed
    elif type == 3:
        embed = discord.Embed(title="Tiempo de espera agotado.", description=f"Hay un tiempo de espera, quedan **{arg}**.", colour=discord.Colour.red())
        return embed
    elif type == 4:
        embed = discord.Embed(title="No hay permisos.", description=f"No tienes permisos para usar este comando, se ha avisado al dueño.", colour=discord.Colour.red())
        return embed

async def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%dh %2dm %2ds" % (hour, minutes, seconds)

async def log(event, user=None, info=None): # logging in log.txt if you want to edit them
    now = datetime.now()
    timedata = f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    writeable = ""
    
    if event == "generated":
        writeable += "[ GENERADO ] "
    elif event == "cooldown":
        writeable += "[ TIEMPO DE ESPERA ] "
    elif event == "no stock":
        writeable += "[ SIN STOCK ] "
    elif event == "no dms":
        writeable += "[  NO DMS  ] "
    elif event == "bootup":
        writeable += "\n[  BOT INICIADO  ] "
    elif event == "ping":
        writeable += "[   PING   ] "
    elif event == "no perms":
        writeable += "[ SIN PERMISOS ] "
    elif event == "userinfo":
        writeable += "[ INFORMACION DEL USUARIO ] "
    elif event == "error":
        writeable += "[ ERROR CRITICO ] "

    writeable += timedata
    
    try:
        writeable += f" ID: {user.id} User: {user.name}#{user.discriminator} // "
    except:
        writeable += f" // "
    
    if event == "generated":
        info = info.strip('\n')
        writeable += f"El usuario recibió el código con éxito: {info}"
    elif event == "cooldown":
        writeable += f"No se pudo enviar un código al usuario porque está en un tiempo de reutilización de {info}."
    elif event == "no stock":
        writeable += f"No se pudo enviar el código al usuario porque no hay stock."
    elif event == "no dms":
        writeable += f"No se pudo enviar un código al usuario porque sus DM estaban deshabilitados."
    elif event == "bootup":
        writeable += "El bot fue encendido."
    elif event == "ping":
        writeable += "El usuario usó el comando ping."
    elif event == "no perms":
        writeable += f"El usuario no tiene los permisos significativos para el comando {info} ."
    elif event == "userinfo":
        writeable += f"El usuario usó el comando userinfo en: {info}"
    elif event == "error":
        writeable += info

    async with aiofiles.open(LOG_FILE, mode="a") as file:
        await file.write(f"\n{writeable}")
    
    if writeable.startswith("[ SIN STOCK ]"):
        print(Fore.LIGHTYELLOW_EX + writeable.strip('\n'))
    elif writeable.startswith("[ ERROR CRITICO ]"):
        for x in range(3):
            print(Fore.LIGHTRED_EX + writeable.strip('\n'))
    elif writeable.startswith("[  BOT INICIADO  ]"):
        print(Fore.LIGHTGREEN_EX + writeable.strip('\n'))

@bot.event
async def on_ready():
    global gen_role
    try:
        open(LOG_FILE, "x").close()
    except:
        pass
    try:
        open(CODES_FILE, "x").close()
    except:
        pass
    await log("bootup")
    for guild in bot.guilds:
        role = guild.get_role(ROLE_ID)
        if role != None:
            gen_role = role
            break
    if gen_role == None:
        await log("error", user=None, info=f"No se puede encontrar el rol ({ROLE_ID}) desde {bot.guilds[0].name}. Saliendo en 5 segundos.")
        await asyncio.sleep(5)
        exit()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        time_retry = await convert(error.retry_after)
        await ctx.send(content = ctx.author.mention, embed = await getEmbed(3, time_retry))
        await log("cooldown", ctx.author, time_retry)
    elif isinstance(error, commands.MissingRole):
        await ctx.send(content = ctx.author.mention, embed = await getEmbed(4))
        await log("no perms", ctx.author, "generate")

@bot.command()
@commands.cooldown(1, COOLDOWN) # 1 is codes per cooldown // 86400 is the cooldown time (is in second)
@commands.has_role(ROLE_ID) # role for gen perms
@commands.guild_only()
async def generate(ctx):
    try:
        dm_msg = await ctx.author.send("Procesando información...")
    except:
        embed = discord.Embed(title="DMs estan desactivados!", description="Debes activarlos para recibir el codigo.", colour=discord.Colour.red())
        await ctx.send(content=ctx.author.mention, embed=embed)
        await log("no dms", ctx.author)
        return
    async with aiofiles.open("oro.txt", mode="r") as file: # name of codes file
        file_lines = await file.readlines()
        try:
            code = random.choice(file_lines)
        except:
            await dm_msg.edit(embed=await getEmbed(type=2), content=ctx.author.mention)
            await ctx.send(embed=await getEmbed(type=2), content=ctx.author.mention)
            bot.get_command("viporo").reset_cooldown(ctx)
            await log("no stock", ctx.author)
            return
        else:
            file_lines.remove(code)
    async with aiofiles.open("oro.txt", mode="w") as file: # name of codes file
        for line in file_lines:
            if file_lines[-1] != line:
                await file.write(line) 
            else: 
                await file.write(line.strip("\n"))
    await dm_msg.edit(embed=await getEmbed(type=1,arg=code), content=ctx.author.mention)
    await ctx.send(embed=await getEmbed(type=0), content=ctx.author.mention)
    await log("generated", ctx.author, code)
    
@bot.command()
@commands.cooldown(1, COOLDOWN) # 1 is codes per cooldown // 86400 is the cooldown time (is in second)
@commands.has_role(ROLE_ID) # role for gen perms
@commands.guild_only()
async def generate(ctx):
    try:
        dm_msg = await ctx.author.send("Procesando información...")
    except:
        embed = discord.Embed(title="DMs estan desactivados!", description="Debes activarlos para recibir el codigo.", colour=discord.Colour.red())
        await ctx.send(content=ctx.author.mention, embed=embed)
        await log("no dms", ctx.author)
        return
    async with aiofiles.open("diamante.txt", mode="r") as file: # name of codes file
        file_lines = await file.readlines()
        try:
            code = random.choice(file_lines)
        except:
            await dm_msg.edit(embed=await getEmbed(type=2), content=ctx.author.mention)
            await ctx.send(embed=await getEmbed(type=2), content=ctx.author.mention)
            bot.get_command("vipdiamante").reset_cooldown(ctx)
            await log("no stock", ctx.author)
            return
        else:
            file_lines.remove(code)
    async with aiofiles.open("diamante.txt", mode="w") as file: # name of codes file
        for line in file_lines:
            if file_lines[-1] != line:
                await file.write(line) 
            else: 
                await file.write(line.strip("\n"))
    await dm_msg.edit(embed=await getEmbed(type=1,arg=code), content=ctx.author.mention)
    await ctx.send(embed=await getEmbed(type=0), content=ctx.author.mention)
    await log("generated", ctx.author, code)
    
@bot.command()
@commands.cooldown(1, COOLDOWN) # 1 is codes per cooldown // 86400 is the cooldown time (is in second)
@commands.has_role(ROLE_ID) # role for gen perms
@commands.guild_only()
async def generate(ctx):
    try:
        dm_msg = await ctx.author.send("Procesando información...")
    except:
        embed = discord.Embed(title="DMs estan desactivados!", description="Debes activarlos para recibir el codigo.", colour=discord.Colour.red())
        await ctx.send(content=ctx.author.mention, embed=embed)
        await log("no dms", ctx.author)
        return
    async with aiofiles.open("plata.txt", mode="r") as file: # name of codes file
        file_lines = await file.readlines()
        try:
            code = random.choice(file_lines)
        except:
            await dm_msg.edit(embed=await getEmbed(type=2), content=ctx.author.mention)
            await ctx.send(embed=await getEmbed(type=2), content=ctx.author.mention)
            bot.get_command("vipplata").reset_cooldown(ctx)
            await log("no stock", ctx.author)
            return
        else:
            file_lines.remove(code)
    async with aiofiles.open("plata.txt", mode="w") as file: # name of codes file
        for line in file_lines:
            if file_lines[-1] != line:
                await file.write(line) 
            else: 
                await file.write(line.strip("\n"))
    await dm_msg.edit(embed=await getEmbed(type=1,arg=code), content=ctx.author.mention)
    await ctx.send(embed=await getEmbed(type=0), content=ctx.author.mention)
    await log("generated", ctx.author, code)

@bot.command()
async def userinfo(ctx, *, user : discord.Member = None):
    if user == None:
        user = ctx.author
    
    if gen_role in user.roles:
        des = f"Generador: `🟢`"
    else:
        des = f"Generador: `🔴`"
    
    embed = discord.Embed(color=discord.Colour.blue(), description=des, title=" ")
    embed.set_author(name=f"{user.name}#{user.discriminator}", icon_url=user.default_avatar_url)
    await ctx.send(embed=embed, content=ctx.author.mention)
    await log("userinfo", user=ctx.author, info=f"{user.name}#{user.discriminator}")

@bot.command()
async def ping(ctx):
    embed = discord.Embed(title="Response Times", color=discord.Colour.blue()) # colour of ping command
    embed.add_field(name="API", value=f"`Loading...`")
    embed.add_field(name="Websocket", value=f"`{int(bot.latency * 1000)}ms`")
    time_before = time.time()
    edit = await ctx.send(embed=embed, content=f"{ctx.author.mention}")
    time_after = time.time()
    difference = int((time_after - time_before) * 1000)
    embed = discord.Embed(title="Response Times", color=discord.Colour.green()) # colour of ping command
    embed.add_field(name="API", value=f"`{difference}ms`")
    embed.add_field(name="Websocket", value=f"`{int(bot.latency * 1000)}ms`")
    await edit.edit(embed=embed, content=f"{ctx.author.mention}")
    await log("ping", ctx.author)

bot.run(TOKEN)
