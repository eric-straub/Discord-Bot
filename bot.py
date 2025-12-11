import os
import logging
import json

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configure logging — DEBUG is helpful while developing
logging.basicConfig(level=logging.DEBUG)

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
        )

    async def on_error(self, event_method, *args, **kwargs):
        """Catch unexpected errors in event handlers."""
        import traceback

        print(f"Unhandled exception in event: {event_method}")
        traceback.print_exc()

    async def on_member_join_autorole(self, member: discord.Member):
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
            print(f"Autorole assignment failed: {e}")

    async def on_socket_response(self, msg):
        """
        Log important gateway events to help debug interaction issues.
        Shows INTERACTION_CREATE, command registration, and READY events.
        """
        try:
            t = msg.get("t")
            op = msg.get("op")

            if t in ("INTERACTION_CREATE", "APPLICATION_COMMAND_CREATE", "READY"):
                print(
                    f"[socket] t={t} op={op} "
                    f"d_keys={list(msg.get('d', {}).keys()) if isinstance(msg.get('d'), dict) else None}"
                )
            else:
                # Keep other events short to avoid spam
                if op is not None:
                    print(f"[socket] op={op} t={t}")
        except Exception as e:
            print(f"on_socket_response logging failed: {e}")

    async def setup_hook(self):
        """Runs before the bot connects — load cogs here."""
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.rank")
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.fun")
        await self.load_extension("cogs.info")
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.economy")
        await self.load_extension("cogs.settings")


# Create bot instance
bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    # Sync slash commands on startup
    await bot.tree.sync()
    print("Slash commands synced.")
    print("Bot is ready.")


bot.run(TOKEN)
