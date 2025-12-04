import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        # self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Register commands globally
        await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

bot.run(TOKEN)
