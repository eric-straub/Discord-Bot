"""Settings cog — bot configuration and server settings."""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os

SETTINGS_FILE = "data/settings.json"
os.makedirs("data", exist_ok=True)


def load_settings():
    """Load settings from JSON."""
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)


def save_settings(data):
    """Save settings to JSON."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)


class Settings(commands.Cog):
    """Server settings and configuration."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    def _ensure_guild(self, guild_id: int):
        """Ensure a guild exists in settings."""
        gid = str(guild_id)
        if gid not in self.settings:
            self.settings[gid] = {
                "prefix": "!",
                "xp_enabled": True,
                "modlog_channel": None,
                "autorole_enabled": False,
                "autorole_id": None
            }
            save_settings(self.settings)

    @app_commands.command(name="config_show", description="Show server configuration")
    async def config_show(self, interaction: discord.Interaction):
        """Display current server settings."""
        gid = str(interaction.guild.id)
        self._ensure_guild(interaction.guild.id)
        config = self.settings[gid]

        modlog_ch = None
        if config.get("modlog_channel"):
            modlog_ch = interaction.guild.get_channel(int(config["modlog_channel"]))
            modlog_ch = modlog_ch.mention if modlog_ch else f"(missing: {config['modlog_channel']})"

        autorole = None
        if config.get("autorole_id"):
            autorole = interaction.guild.get_role(int(config["autorole_id"]))
            autorole = autorole.mention if autorole else f"(missing: {config['autorole_id']})"

        embed = discord.Embed(
            title=f"⚙️ Server Configuration — {interaction.guild.name}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Prefix", value=f"`{config.get('prefix', '!')}`", inline=True)
        embed.add_field(name="XP Enabled", value="✅" if config.get("xp_enabled", True) else "❌", inline=True)
        embed.add_field(name="Modlog Channel", value=modlog_ch or "Not set", inline=True)
        embed.add_field(name="Autorole", value=autorole or "Not set", inline=True)
        embed.add_field(name="Autorole Enabled", value="✅" if config.get("autorole_enabled", False) else "❌", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_xp_enabled", description="Enable or disable XP rewards (admin only)")
    async def set_xp_enabled(self, interaction: discord.Interaction, enabled: bool):
        """Toggle XP gain for the server."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Missing permissions (administrator).",
                ephemeral=True
            )
            return

        gid = str(interaction.guild.id)
        self._ensure_guild(interaction.guild.id)
        self.settings[gid]["xp_enabled"] = enabled
        save_settings(self.settings)

        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"XP rewards {status} for this server.")

    @app_commands.command(name="set_modlog_channel", description="Set the modlog channel (admin only)")
    async def set_modlog_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Set where moderation logs should be posted. Omit channel to disable."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Missing permissions (administrator).",
                ephemeral=True
            )
            return

        gid = str(interaction.guild.id)
        self._ensure_guild(interaction.guild.id)
        self.settings[gid]["modlog_channel"] = channel.id if channel else None
        save_settings(self.settings)

        if channel:
            await interaction.response.send_message(f"Modlog channel set to {channel.mention}.")
        else:
            await interaction.response.send_message("Modlog channel disabled.")

    @app_commands.command(name="set_autorole", description="Set automatic role for new members (admin only)")
    async def set_autorole(self, interaction: discord.Interaction, role: discord.Role = None):
        """Automatically assign a role to new members. Omit role to disable."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Missing permissions (administrator).",
                ephemeral=True
            )
            return

        gid = str(interaction.guild.id)
        self._ensure_guild(interaction.guild.id)
        
        if role:
            self.settings[gid]["autorole_id"] = role.id
            self.settings[gid]["autorole_enabled"] = True
            save_settings(self.settings)
            await interaction.response.send_message(f"New members will be assigned {role.mention}.")
        else:
            self.settings[gid]["autorole_enabled"] = False
            self.settings[gid]["autorole_id"] = None
            save_settings(self.settings)
            await interaction.response.send_message("Autorole disabled.")


async def setup(bot):
    await bot.add_cog(Settings(bot))
