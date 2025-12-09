import os
import json
import discord
from discord.ext import commands
from discord import app_commands

WELCOME_FILE = "data/welcome.json"
os.makedirs("data", exist_ok=True)

def load_welcome():
    if not os.path.exists(WELCOME_FILE):
        return {}
    with open(WELCOME_FILE, "r") as f:
        return json.load(f)

def save_welcome(data):
    with open(WELCOME_FILE, "w") as f:
        json.dump(data, f, indent=4)


class Welcome(commands.Cog):
    """Welcome cog: per-guild welcome message stored in `data/welcome.json`.

    Data shape:
      guild_id -> { "enabled": bool, "channel_id": int|null, "message": str }
    If `channel_id` is null the bot will DM new members; otherwise it will post in the channel.
    Message placeholders: `{user}` (mention), `{name}` (display name), `{guild}` (guild name).
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = load_welcome()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        gid = str(guild.id)
        cfg = self.config.get(gid)
        if not cfg or not cfg.get("enabled"):
            return

        message = cfg.get("message", "Welcome {user} to {guild}!")
        # Replace placeholders
        message = message.replace("{user}", member.mention).replace("{name}", member.display_name).replace("{guild}", guild.name)

        channel_id = cfg.get("channel_id")
        try:
            if channel_id is None:
                # DM the user
                await member.send(message)
            else:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(message)
        except Exception:
            # Don't raise in event handler
            return

    # Admin: set welcome message
    @app_commands.command(name="welcome_set", description="Set the server welcome message")
    async def welcome_set(self, interaction: discord.Interaction, *, message: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
            return

        gid = str(interaction.guild.id)
        cfg = self.config.get(gid, {})
        cfg["message"] = message
        # Ensure keys
        cfg.setdefault("enabled", True)
        cfg.setdefault("channel_id", None)
        self.config[gid] = cfg
        save_welcome(self.config)
        await interaction.response.send_message("Welcome message updated.")

    # Admin: set channel (optional). If channel omitted, sets to DM mode.
    @app_commands.command(name="welcome_set_channel", description="Set channel for welcome messages (omit for DM)")
    async def welcome_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
            return

        gid = str(interaction.guild.id)
        cfg = self.config.get(gid, {})
        cfg.setdefault("enabled", True)
        cfg["channel_id"] = channel.id if channel else None
        self.config[gid] = cfg
        save_welcome(self.config)
        where = f"#{channel.name}" if channel else "DMs"
        await interaction.response.send_message(f"Welcome messages will be sent to {where}.")

    # Admin: enable/disable welcome
    @app_commands.command(name="welcome_toggle", description="Enable or disable welcome messages")
    async def welcome_toggle(self, interaction: discord.Interaction, enabled: bool):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
            return

        gid = str(interaction.guild.id)
        cfg = self.config.get(gid, {})
        cfg["enabled"] = enabled
        cfg.setdefault("channel_id", None)
        cfg.setdefault("message", "Welcome {user} to {guild}!")
        self.config[gid] = cfg
        save_welcome(self.config)
        await interaction.response.send_message(f"Welcome messages {'enabled' if enabled else 'disabled'}.")

    @app_commands.command(name="welcome_show", description="Show the current welcome configuration")
    async def welcome_show(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        cfg = self.config.get(gid)
        if not cfg:
            await interaction.response.send_message("No welcome configuration set for this server.")
            return

        enabled = cfg.get("enabled", False)
        channel_id = cfg.get("channel_id")
        channel_name = None
        if channel_id is None:
            channel_name = "DMs"
        else:
            ch = interaction.guild.get_channel(int(channel_id))
            channel_name = ch.mention if ch else f"(missing channel {channel_id})"

        message = cfg.get("message", "")
        embed = discord.Embed(title=f"Welcome Config for {interaction.guild.name}", color=discord.Color.green())
        embed.add_field(name="Enabled", value=str(enabled), inline=True)
        embed.add_field(name="Channel", value=channel_name, inline=True)
        embed.add_field(name="Message", value=message or "(empty)", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
