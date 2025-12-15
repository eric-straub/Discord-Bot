"""Moderation cog — warns, kicks, timeouts, and cleanup utilities."""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import timedelta, datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import is_admin

WARN_FILE = "data/warns.json"
os.makedirs("data", exist_ok=True)


def load_warns():
    """Load warnings from JSON."""
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)


def save_warns(data):
    """Save warnings to JSON."""
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)


class Moderation(commands.Cog):
    """Moderation tools and commands."""

    def __init__(self, bot):
        self.bot = bot
        self.warns = load_warns()

    def _require_mod(self, interaction: discord.Interaction) -> bool:
        """Check if user has moderate_members permission or is an admin."""
        return is_admin(interaction.user.id) or interaction.user.guild_permissions.moderate_members

    @app_commands.command(name="warn", description="Warn a member (mod only)")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = "No reason provided"):
        """Add a warning to a member."""
        if not self._require_mod(interaction):
            await interaction.response.send_message("Missing permissions (moderate_members).", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("Cannot warn bots.", ephemeral=True)
            return

        gid = str(interaction.guild.id)
        uid = str(member.id)

        if gid not in self.warns:
            self.warns[gid] = {}
        if uid not in self.warns[gid]:
            self.warns[gid][uid] = []

        self.warns[gid][uid].append({
            "reason": reason,
            "issued_by": str(interaction.user.id),
            "timestamp": datetime.utcnow().isoformat()
        })

        save_warns(self.warns)

        warn_count = len(self.warns[gid][uid])
        embed = discord.Embed(
            title="⚠️ Member Warned",
            color=discord.Color.orange(),
            description=f"{member.mention} has been warned.\n**Reason:** {reason}"
        )
        embed.add_field(name="Total Warnings", value=str(warn_count), inline=True)
        embed.add_field(name="Warned By", value=interaction.user.mention, inline=True)

        await interaction.response.send_message(embed=embed)

        # Try to DM the member
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ Warning in {interaction.guild.name}",
                color=discord.Color.orange(),
                description=f"You have received a warning.\n**Reason:** {reason}\n**Total Warnings:** {warn_count}"
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # Can't DM

    @app_commands.command(name="warns", description="Check warnings for a member (mod only)")
    async def warns(self, interaction: discord.Interaction, member: discord.Member = None):
        """View all warnings for a member."""
        if not self._require_mod(interaction):
            await interaction.response.send_message("Missing permissions (moderate_members).", ephemeral=True)
            return

        member = member or interaction.user
        gid = str(interaction.guild.id)
        uid = str(member.id)

        warns_list = self.warns.get(gid, {}).get(uid, [])

        if not warns_list:
            await interaction.response.send_message(f"No warnings found for {member.mention}.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"⚠️ Warnings for {member.display_name}",
            color=discord.Color.orange()
        )

        for i, warn in enumerate(warns_list, 1):
            issued_by_id = warn.get("issued_by", "Unknown")
            issued_by_user = interaction.guild.get_member(int(issued_by_id))
            issued_by = issued_by_user.mention if issued_by_user else f"User {issued_by_id}"
            reason = warn.get("reason", "No reason")
            timestamp = warn.get("timestamp", "Unknown")

            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Reason:** {reason}\n**By:** {issued_by}\n**Time:** {timestamp[:10]}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearwarn", description="Remove all warnings from a member (mod only)")
    async def clearwarn(self, interaction: discord.Interaction, member: discord.Member):
        """Clear all warnings for a member."""
        if not self._require_mod(interaction):
            await interaction.response.send_message("Missing permissions (moderate_members).", ephemeral=True)
            return

        gid = str(interaction.guild.id)
        uid = str(member.id)

        if gid not in self.warns or uid not in self.warns[gid]:
            await interaction.response.send_message(f"No warnings to clear for {member.mention}.", ephemeral=True)
            return

        del self.warns[gid][uid]
        save_warns(self.warns)

        await interaction.response.send_message(f"Cleared all warnings for {member.mention}.")

    @app_commands.command(name="timeout", description="Timeout a member (mute for a duration)")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, *, duration: str = "1h"):
        """Timeout (mute) a member for a specified duration. Format: 1h, 30m, 1d, etc."""
        if not self._require_mod(interaction):
            await interaction.response.send_message("Missing permissions (moderate_members).", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("Cannot timeout bots.", ephemeral=True)
            return

        # Parse duration
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            if unit == "m":
                timeout_duration = timedelta(minutes=amount)
            elif unit == "h":
                timeout_duration = timedelta(hours=amount)
            elif unit == "d":
                timeout_duration = timedelta(days=amount)
            else:
                raise ValueError("Invalid unit")
        except (ValueError, IndexError):
            await interaction.response.send_message("Invalid duration format. Use: 1h, 30m, 1d, etc.", ephemeral=True)
            return

        try:
            await member.timeout(timeout_duration)
            embed = discord.Embed(
                title="⏱️ Member Timed Out",
                color=discord.Color.red(),
                description=f"{member.mention} has been timed out for {duration}."
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("Cannot timeout this member (insufficient permissions).", ephemeral=True)

    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):
        """Remove timeout (mute) from a member."""
        if not self._require_mod(interaction):
            await interaction.response.send_message("Missing permissions (moderate_members).", ephemeral=True)
            return

        try:
            await member.timeout(None)
            await interaction.response.send_message(f"Timeout removed from {member.mention}.")
        except discord.Forbidden:
            await interaction.response.send_message("Cannot remove timeout (insufficient permissions).", ephemeral=True)

    @app_commands.command(name="purge", description="Delete recent messages in the channel (mod only)")
    async def purge(self, interaction: discord.Interaction, count: int = 10):
        """Delete the last N messages in the current channel."""
        if not self._require_mod(interaction):
            await interaction.response.send_message("Missing permissions (moderate_members).", ephemeral=True)
            return

        if count < 1 or count > 100:
            await interaction.response.send_message("Purge count must be between 1 and 100.", ephemeral=True)
            return

        # Defer since purge can take a moment
        await interaction.response.defer()

        deleted = await interaction.channel.purge(limit=count)
        await interaction.followup.send(f"Purged {len(deleted)} messages.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
