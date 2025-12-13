"""Economy cog — currency, wallets, and transactions."""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time
from datetime import datetime, timedelta

ECONOMY_FILE = "data/economy.json"
os.makedirs("data", exist_ok=True)

# Currency name
CURRENCY_NAME = "🪙 Credits"
DAILY_REWARD = 100


def load_economy():
    """Load economy data from JSON."""
    if not os.path.exists(ECONOMY_FILE):
        return {}
    with open(ECONOMY_FILE, "r") as f:
        return json.load(f)


def save_economy(data):
    """Save economy data to JSON."""
    with open(ECONOMY_FILE, "w") as f:
        json.dump(data, f, indent=4)


class Economy(commands.Cog):
    """Currency and economy system."""

    def __init__(self, bot):
        self.bot = bot
        self.economy = load_economy()
        self.daily_cooldowns = {}  # user_id: timestamp

    def _ensure_user(self, user_id: int):
        """Ensure a user exists in the economy system."""
        uid = str(user_id)
        if uid not in self.economy:
            self.economy[uid] = {"balance": 0, "total_earned": 0}

    def _add_balance(self, user_id: int, amount: int):
        """Add currency to a user's balance."""
        uid = str(user_id)
        self._ensure_user(user_id)
        self.economy[uid]["balance"] += amount
        self.economy[uid]["total_earned"] += max(0, amount)
        save_economy(self.economy)

    def _remove_balance(self, user_id: int, amount: int) -> bool:
        """Remove currency from a user's balance. Returns True if successful."""
        uid = str(user_id)
        self._ensure_user(user_id)
        if self.economy[uid]["balance"] < amount:
            return False
        self.economy[uid]["balance"] -= amount
        save_economy(self.economy)
        return True

    @app_commands.command(name="balance", description="Check your wallet balance")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        """View your or another user's current balance."""
        member = member or interaction.user
        uid = str(member.id)
        self._ensure_user(member.id)

        balance = self.economy[uid]["balance"]
        total_earned = self.economy[uid]["total_earned"]

        embed = discord.Embed(
            title=f"{member.display_name}'s Wallet",
            color=discord.Color.gold()
        )
        embed.add_field(name="Balance", value=f"{CURRENCY_NAME} {balance}", inline=True)
        embed.add_field(name="Total Earned", value=f"{CURRENCY_NAME} {total_earned}", inline=True)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily bonus")
    async def daily(self, interaction: discord.Interaction):
        """Claim a daily bonus (once per 24 hours)."""
        uid = interaction.user.id
        now = time.time()

        last_claim = self.daily_cooldowns.get(uid, 0)
        if now - last_claim < 86400:  # 24 hours in seconds
            hours_left = (86400 - (now - last_claim)) / 3600
            await interaction.response.send_message(
                f"You've already claimed today! Come back in {hours_left:.1f} hours.",
                ephemeral=True
            )
            return

        self._add_balance(interaction.user.id, DAILY_REWARD)
        self.daily_cooldowns[uid] = now

        embed = discord.Embed(
            title="Daily Bonus Claimed!",
            color=discord.Color.green(),
            description=f"You received {CURRENCY_NAME} {DAILY_REWARD}"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Send currency to another user")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        """Transfer currency to another user."""
        if member.bot:
            await interaction.response.send_message("Cannot send currency to bots.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return

        # Check sender has enough
        if not self._remove_balance(interaction.user.id, amount):
            await interaction.response.send_message(
                f"Insufficient balance! You have {self.economy[str(interaction.user.id)]['balance']} {CURRENCY_NAME}.",
                ephemeral=True
            )
            return

        # Add to recipient
        self._add_balance(member.id, amount)

        embed = discord.Embed(
            title="💸 Payment Sent",
            color=discord.Color.blue(),
            description=f"Sent {CURRENCY_NAME} {amount} to {member.mention}"
        )
        await interaction.response.send_message(embed=embed)

        # Notify recipient
        try:
            dm_embed = discord.Embed(
                title="💸 Payment Received",
                color=discord.Color.green(),
                description=f"{interaction.user.mention} sent you {CURRENCY_NAME} {amount}"
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    @app_commands.command(name="rich", description="Show the wealthiest users")
    async def rich(self, interaction: discord.Interaction):
        """Display the richest members by balance."""
        self._ensure_user(interaction.user.id)

        sorted_users = sorted(
            self.economy.items(),
            key=lambda x: x[1]["balance"],
            reverse=True
        )

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server (guild).", ephemeral=True)
            return

        guild_users = [(uid, data) for uid, data in sorted_users if guild.get_member(int(uid))]

        if not guild_users:
            await interaction.response.send_message("No economy data for members on this server.")
            return

        embed = discord.Embed(
            title="💰 Richest Members",
            color=discord.Color.gold()
        )

        for i, (user_id, data) in enumerate(guild_users[:10], start=1):
            user = guild.get_member(int(user_id))
            name = user.display_name if user else f"Unknown ({user_id})"
            balance = data["balance"]
            embed.add_field(
                name=f"#{i} — {name}",
                value=f"{CURRENCY_NAME} {balance}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give_currency", description="Give currency to a user (admin only)")
    async def give_currency(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        """Admin command to grant currency."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Missing permissions (administrator).",
                ephemeral=True
            )
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return

        self._add_balance(member.id, amount)
        await interaction.response.send_message(
            f"Gave {CURRENCY_NAME} {amount} to {member.mention}"
        )

    @app_commands.command(name="reset_economy", description="Reset all economy data (admin only)")
    async def reset_economy(self, interaction: discord.Interaction, confirm: bool = False):
        """Reset all currency balances (requires confirmation)."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Missing permissions (administrator).",
                ephemeral=True
            )
            return

        if not confirm:
            await interaction.response.send_message(
                "⚠️ This will reset all user balances! Run again with `confirm:True` to proceed.",
                ephemeral=True
            )
            return

        self.economy = {}
        save_economy(self.economy)
        await interaction.response.send_message("✅ Economy data reset.")


async def setup(bot):
    await bot.add_cog(Economy(bot))
