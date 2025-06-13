import discord
from discord.ext import commands
from discord import app_commands, Interaction
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

print("Defining /ping command")
@tree.command(name="ping", description="Antwortet mit Pong!")
async def ping(interaction: Interaction):
    print("Ping command invoked")
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

@bot.event
async def on_ready():
    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        synced = await tree.sync(guild=guild)
        print(f"Synchronized {len(synced)} commands with guild {guild_id}: {[cmd.name for cmd in synced]}")
    else:
        synced = await tree.sync()
        print(f"Synchronized {len(synced)} global commands: {[cmd.name for cmd in synced]}")
    print(f"Bot logged in as {bot.user}")

bot.run(DISCORD_TOKEN)
