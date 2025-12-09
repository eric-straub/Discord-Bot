import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time
import discord

RANK_FILE = "data/ranks.json"   # Ensure this folder exists

def load_ranks():
    if not os.path.exists(RANK_FILE):
        return {}
    with open(RANK_FILE, "r") as f:
        return json.load(f)

def save_ranks(data):
    with open(RANK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def calculate_level(xp: int) -> int:
    # Level curve: level = sqrt(xp / 50)
    return int((xp / 50) ** 0.5)


class RankSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ranks = load_ranks()
        self.cooldowns = {}  # user_id: timestamp

    async def award_xp(self, user_id: int, amount: int):
        """Add XP and check for level-up."""
        user_id = str(user_id)

        if user_id not in self.ranks:
            self.ranks[user_id] = {"xp": 0, "level": 0}

        user = self.ranks[user_id]
        old_level = user["level"]

        # Add XP
        user["xp"] += amount
        user["level"] = calculate_level(user["xp"])

        save_ranks(self.ranks)

        # Level up!
        if user["level"] > old_level:
            return user["level"]
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Award XP per message with cooldown to prevent spam abuse."""
        if message.author.bot:
            return

        user_id = message.author.id
        now = time.time()

        # 10-second XP cooldown per user
        last = self.cooldowns.get(user_id, 0)
        if now - last < 10:
            return

        self.cooldowns[user_id] = now

        # XP between 15 and 25 per message
        import random
        xp_gain = random.randint(15, 25)

        new_level = await self.award_xp(user_id, xp_gain)
        if new_level:
            await message.channel.send(
                f"🎉 **{message.author.mention} leveled up to Level {new_level}!**"
            )

    # Slash Command: /rank
    @app_commands.command(name="rank", description="Check your XP and level")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user

        user_id = str(member.id)
        stats = self.ranks.get(user_id, {"xp": 0, "level": 0})

        embed = discord.Embed(
            title=f"{member.display_name}'s Rank",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Level", value=stats["level"])
        embed.add_field(name="XP", value=stats["xp"])
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Show a user's profile (XP, level, parries)")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        user_id = str(member.id)
        stats = self.ranks.get(user_id, {"xp": 0, "level": 0})

        embed = discord.Embed(title=f"{member.display_name}'s Profile", color=discord.Color.blurple())
        embed.add_field(name="Level", value=stats["level"])
        embed.add_field(name="XP", value=stats["xp"])
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="xp_set", description="Set a user's XP (admin only)")
    async def xp_set(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
            return

        uid = str(member.id)
        if uid not in self.ranks:
            self.ranks[uid] = {"xp": 0, "level": 0}
        self.ranks[uid]["xp"] = max(0, amount)
        self.ranks[uid]["level"] = calculate_level(self.ranks[uid]["xp"])
        save_ranks(self.ranks)
        await interaction.response.send_message(f"Set {member.display_name}'s XP to {self.ranks[uid]['xp']} (Level {self.ranks[uid]['level']}).")

    @app_commands.command(name="xp_add", description="Add XP to a user (admin only)")
    async def xp_add(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
            return

        uid = str(member.id)
        if uid not in self.ranks:
            self.ranks[uid] = {"xp": 0, "level": 0}
        self.ranks[uid]["xp"] = max(0, self.ranks[uid]["xp"] + amount)
        old_level = self.ranks[uid]["level"]
        self.ranks[uid]["level"] = calculate_level(self.ranks[uid]["xp"])
        save_ranks(self.ranks)
        await interaction.response.send_message(f"Added {amount} XP to {member.display_name}. Level: {old_level} → {self.ranks[uid]['level']}")

    @app_commands.command(name="xp_recalc", description="Recalculate levels for all users from XP (admin only)")
    async def xp_recalc(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
            return

        for uid, data in self.ranks.items():
            data["level"] = calculate_level(data.get("xp", 0))
        save_ranks(self.ranks)
        await interaction.response.send_message("Recalculated levels for all users.")

    # Slash Command: /leaderboard
    @app_commands.command(name="leaderboard", description="Show the top users by level")
    async def leaderboard(self, interaction: discord.Interaction):
        sorted_users = sorted(
            self.ranks.items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )

        embed = discord.Embed(
            title="🏆 Server Leaderboard",
            color=discord.Color.gold()
        )

        for i, (user_id, data) in enumerate(sorted_users[:10], start=1):
            user = interaction.guild.get_member(int(user_id))
            name = user.display_name if user else f"Unknown ({user_id})"

            embed.add_field(
                name=f"#{i} — {name}",
                value=f"Level {data['level']} • {data['xp']} XP",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(RankSystem(bot))
