import os
import logging
import json

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Bot version
__version__ = "0.0.2-alpha"

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configure logging - INFO level to reduce noise, DEBUG for development
logging.basicConfig(level=logging.INFO)

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=os.getenv("APPLICATION_ID"),
            help_command=None,  # Disable built-in help command to avoid conflicts
        )
        self.version = __version__

    async def on_error(self, event_method, *args, **kwargs):
        """Catch unexpected errors in event handlers."""
        import traceback

        print(f"Unhandled exception in event: {event_method}")
        traceback.print_exc()

    async def on_member_join(self, member: discord.Member):
        """Auto-assign role to new members if configured."""
        try:
            settings_file = "data/settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                    gid = str(member.guild.id)
                    config = settings.get(gid, {})
                    if config.get("autorole_enabled") and config.get("autorole_id"):
                        role = member.guild.get_role(int(config["autorole_id"]))
                        if role:
                            await member.add_roles(role)
                            print(f"[autorole] Assigned {role.name} to {member}")
        except Exception as e:
            print(f"[autorole] Failed to assign role: {e}")

    async def on_socket_response(self, msg):
        """
        Log important gateway events to help debug interaction issues.
        Only logs INTERACTION_CREATE, APPLICATION_COMMAND_CREATE, and READY events.
        """
        try:
            t = msg.get("t")
            if t in ("INTERACTION_CREATE", "APPLICATION_COMMAND_CREATE", "READY"):
                op = msg.get("op")
                d_keys = list(msg.get('d', {}).keys()) if isinstance(msg.get('d'), dict) else None
                print(f"[socket] t={t} op={op} d_keys={d_keys}")
        except Exception as e:
            print(f"[socket] Logging failed: {e}")

    async def setup_hook(self):
        """Runs before the bot connects — load cogs here."""
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.rank")
        await self.load_extension("cogs.fun")
        await self.load_extension("cogs.games")
        await self.load_extension("cogs.economy")
        await self.load_extension("cogs.trivia")
        await self.load_extension("cogs.casino")


# Create bot instance
bot = MyBot()


@bot.event
async def on_ready():
    if bot.user is None:
        print("Error: bot.user is None in on_ready event")
        return
    
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    # Sync slash commands on startup
    await bot.tree.sync()
    print("Slash commands synced.")
    print("Bot is ready.")

if TOKEN is None:
    print("Error: DISCORD_TOKEN not found in environment variables.")
    print("Please create a .env file with DISCORD_TOKEN set.")
    exit(1)

bot.run(TOKEN)
