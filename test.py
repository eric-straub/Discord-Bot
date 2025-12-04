import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # If you want instant sync for testing, use your guild ID instead:
        # guild = discord.Object(id=YOUR_GUILD_ID)
        # await self.tree.sync(guild=guild)
        
        await self.tree.sync()  # Global sync (takes up to 1 hour)
        print("Slash commands synced.")

bot = MyBot(command_prefix="!", intents=intents)

@bot.tree.command(name="hello", description="Say hello")
async def hello_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

bot.run(TOKEN)
