import os
import sys
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import api_client
import commands as bot_commands

# Check if the script is running inside a PyInstaller EXE bundle
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS # Hidden runtime extraction folder
    env_path = os.path.join(bundle_dir, '.env')
    load_dotenv(env_path)
else:
    # Running normally as a raw .py script
    load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ALLOWED_CHANNEL_ID = int(os.getenv("PALWORLD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🎉 Success! Bot is online as {bot.user}")
    # 1. Load the extension first
    await bot.load_extension('commands')
    
    # 2. Get the Cog instance
    cog = bot.get_cog("ServerControl")

    if api_client.is_server_process_running():
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Palworld Server (ONLINE)"))
        if cog and not cog.auto_shutdown_check.is_running():
            cog.auto_shutdown_check.start()
            print("Server process detected! Auto-shutdown monitor started.")
    else:
        await bot.change_presence(status=discord.Status.idle, activity=None)

bot.run(BOT_TOKEN)