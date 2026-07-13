import os
import asyncio
import urllib.error
import discord
from discord.ext import commands, tasks
import api_client

ALLOWED_CHANNEL_ID = int(os.getenv("PALWORLD_CHANNEL_ID"))
SERVER_EXE_PATH = os.getenv("PALWORLD_EXE_PATH")
SERVER_DIR = os.getenv("PALWORLD_DIR")
API_PORT = os.getenv("PALWORLD_API_PORT")

class ServerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.empty_minutes_counter = 0

    @tasks.loop(minutes=1)
    async def auto_shutdown_check(self):
        if not api_client.is_server_process_running():
            self.empty_minutes_counter = 0
            return

        try:
            data = await asyncio.to_thread(api_client.call_palworld_api, "players", method="GET")
            current_players = len(data.get("players", [])) if data and isinstance(data, dict) else 0
            
            # Grab max player setting or default to 32
            max_players = 32

            if current_players > 0:
                self.empty_minutes_counter = 0
                await self.bot.change_presence(
                    status=discord.Status.online, 
                    activity=discord.Game(name=f"Palworld ({current_players}/{max_players} Players)")
                )
            else:
                await self.bot.change_presence(
                    status=discord.Status.online, 
                    activity=discord.Game(name="Palworld (0 Players)")
                )
                self.empty_minutes_counter += 1
                if self.empty_minutes_counter >= 10:
                    print("💤 Automated idle shutdown sequence triggered.")
                    await asyncio.to_thread(api_client.call_palworld_api, "save")
                    await asyncio.to_thread(api_client.call_palworld_api, "shutdown", payload={"waittime": 5, "message": "Inactivity shutdown"})
                    self.empty_minutes_counter = 0
                    await self.bot.change_presence(status=discord.Status.idle, activity=None)
        except Exception:
            pass
        
    @commands.command(name="start")
    async def start_server(self, ctx):
        if ctx.channel.id != ALLOWED_CHANNEL_ID: return
        
        is_running = await asyncio.to_thread(api_client.is_server_process_running)
        if is_running:
            await ctx.send("🤖 System check: The Palworld server process is already running on the host PC!")
            return

        try:
            import subprocess
            subprocess.Popen(
                [SERVER_EXE_PATH, "-publiclobby"],
                cwd=SERVER_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Palworld Server (ONLINE)"))
            self.auto_shutdown_check.start()
            await ctx.send("✅ Game server console spawned successfully!")
        except Exception as e:
            await ctx.send(f"❌ Failed to launch executable: {e}")

    @commands.command(name="stop")
    async def stop_server(self, ctx):
        if ctx.channel.id != ALLOWED_CHANNEL_ID: return

        is_running = await asyncio.to_thread(api_client.is_server_process_running)
        if not is_running:
            await ctx.send("❌ Cannot stop: The server is already completely offline.")
            return

        try:
            await ctx.send("💾 Saving world progress...")
            await asyncio.to_thread(api_client.call_palworld_api, "save")

            shutdown_payload = {"waittime": 5, "message": "Server shutting down"}
            status = await asyncio.to_thread(api_client.call_palworld_api, "shutdown", payload=shutdown_payload)
            
            if status in [200, 202]:
                await self.bot.change_presence(status=discord.Status.idle, activity=None)
                await ctx.send("💤 Success! Server has saved progress and closed down safely.")
                self.auto_shutdown_check.stop()
        except urllib.error.URLError:
            await ctx.send("❌ Failed to reach the server API.")

    @commands.command(name="settings")
    async def server_settings(self, ctx):
        if ctx.channel.id != ALLOWED_CHANNEL_ID: return

        is_running = await asyncio.to_thread(api_client.is_server_process_running)
        if not is_running:
            await ctx.send("❌ Cannot fetch settings: The Palworld server is currently offline.")
            return

        try:
            data = await asyncio.to_thread(api_client.call_palworld_api, "settings", method="GET")
            if not data: return

            embed = discord.Embed(title="⚙️ Palworld Server Configuration", color=discord.Color.blue())
            embed.add_field(name="Difficulty", value=data.get("Difficulty", "Default"), inline=True)
            embed.add_field(name="Max Players", value=data.get("ServerPlayerMaxNum", "32"), inline=True)
            embed.add_field(name="📈 Multipliers", value=f"• **XP Rate:** {data.get('ExpRate', '1.0')}x\n• **Capture Rate:** {data.get('PalCaptureRate', '1.0')}x", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error displaying settings: {e}")

async def setup(bot):
    await bot.add_cog(ServerControl(bot))