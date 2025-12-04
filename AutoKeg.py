import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import logging

# Load env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Setup logging (DEBUG to capture gateway events when diagnosing interactions)
logging.basicConfig(level=logging.DEBUG)

# Bot Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize bot
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=os.getenv("APPLICATION_ID")
        )
        # self.tree = app_commands.CommandTree(self)

    async def on_error(self, event_method, *args, **kwargs):
        # Generic event error logger to capture uncaught exceptions in event handlers
        import traceback
        print(f"Unhandled exception in event: {event_method}")
        traceback.print_exc()

    async def on_socket_response(self, msg):
        """Log raw socket messages (t = event name). Useful to see INTERACTION_CREATE deliveries."""
        try:
            t = msg.get("t")
            op = msg.get("op")
            # Print only relevant events to avoid noise
            if t in ("INTERACTION_CREATE", "APPLICATION_COMMAND_CREATE", "READY"):
                print(f"[socket] t={t} op={op} d_keys={list(msg.get('d', {}).keys()) if isinstance(msg.get('d'), dict) else None}")
            else:
                # Short debug for other opcodes; keep minimal
                if op is not None:
                    print(f"[socket] op={op} t={t}")
        except Exception as e:
            print(f"on_socket_response logging failed: {e}")

    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.general")

        # # Sync slash commands
        # await self.tree.sync()
        # print("Slash commands synced.")

# Create bot instance
bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()
    print("Slash commands synced.")
    print("Bot is ready.")


bot.run(TOKEN)
