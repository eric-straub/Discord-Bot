import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import is_admin

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
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("Missing permissions (admin only).", ephemeral=True)
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
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("Missing permissions (admin only).", ephemeral=True)
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
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("Missing permissions (admin only).", ephemeral=True)
            return

        for uid, data in self.ranks.items():
            data["level"] = calculate_level(data.get("xp", 0))
        save_ranks(self.ranks)
        await interaction.response.send_message("Recalculated levels for all users.")

    # Slash Command: /leaderboard
    @app_commands.command(name="leaderboard", description="Show the top users by level")
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Display the server leaderboard (10 users per page)."""
        sorted_users = sorted(
            self.ranks.items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )

        # Filter to members present in this guild
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server (guild).", ephemeral=True)
            return

        guild_users = [(uid, data) for uid, data in sorted_users if guild.get_member(int(uid))]

        # Pagination
        per_page = 10
        total_pages = (len(guild_users) + per_page - 1) // per_page
        if total_pages == 0:
            await interaction.response.send_message("No ranked members found on this server.")
            return

        if page < 1 or page > total_pages:
            page = 1

        start = (page - 1) * per_page
        end = start + per_page

        embed = discord.Embed(
            title="🏆 Server Leaderboard",
            color=discord.Color.gold()
        )

        for i, (user_id, data) in enumerate(guild_users[start:end], start=start + 1):
            user = guild.get_member(int(user_id))
            name = user.display_name if user else f"Unknown ({user_id})"

            embed.add_field(
                name=f"#{i} — {name}",
                value=f"Level {data['level']} • {data['xp']} XP",
                inline=False
            )

        embed.set_footer(text=f"Page {page} of {total_pages}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="topranks", description="Show top 10 players by XP")
    async def topranks(self, interaction: discord.Interaction):
        """Quick view of top 10 ranked players."""
        sorted_users = sorted(
            self.ranks.items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )

        # Filter to guild members
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server (guild).", ephemeral=True)
            return

        guild_users = [(uid, data) for uid, data in sorted_users if guild.get_member(int(uid))]

        text = "🏆 **Top 10 Players**\n\n"
        for i, (user_id, data) in enumerate(guild_users[:10], start=1):
            user = guild.get_member(int(user_id))
            name = user.display_name if user else "Unknown"
            text += f"{i}. {name} — Lvl {data['level']} ({data['xp']} XP)\n"

        if len(guild_users) == 0:
            await interaction.response.send_message("No ranked members found on this server.")
            return

        await interaction.response.send_message(text)

    @app_commands.command(name="xp_leaderboard", description="Show leaderboard sorted by total XP gained")
    async def xp_leaderboard(self, interaction: discord.Interaction):
        """Show top users by raw XP count."""
        sorted_users = sorted(
            self.ranks.items(),
            key=lambda x: x[1].get("xp", 0),
            reverse=True
        )

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server (guild).", ephemeral=True)
            return

        guild_users = [(uid, data) for uid, data in sorted_users if guild.get_member(int(uid))]

        if len(guild_users) == 0:
            await interaction.response.send_message("No ranked members found on this server.")
            return

        embed = discord.Embed(
            title="📊 XP Leaderboard",
            color=discord.Color.purple()
        )

        for i, (user_id, data) in enumerate(guild_users[:15], start=1):
            user = guild.get_member(int(user_id))
            name = user.display_name if user else f"Unknown ({user_id})"
            embed.add_field(
                name=f"#{i} — {name}",
                value=f"{data.get('xp', 0)} XP",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="next_level", description="See how much XP you need for the next level")
    async def next_level(self, interaction: discord.Interaction, member: discord.Member = None):
        """Show progress to next level."""
        member = member or interaction.user
        user_id = str(member.id)
        stats = self.ranks.get(user_id, {"xp": 0, "level": 0})

        current_xp = stats["xp"]
        current_level = stats["level"]
        next_level = current_level + 1

        # XP needed: level = sqrt(xp / 50), so xp = level^2 * 50
        current_level_xp = int((current_level ** 2) * 50)
        next_level_xp = int((next_level ** 2) * 50)

        xp_in_level = current_xp - current_level_xp
        xp_needed = next_level_xp - current_xp

        # Progress bar
        total_in_level = next_level_xp - current_level_xp
        progress = xp_in_level / total_in_level if total_in_level > 0 else 0
        bar_length = 20
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)

        embed = discord.Embed(
            title=f"{member.display_name}'s Progress",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Current Level", value=current_level, inline=True)
        embed.add_field(name="Next Level", value=next_level, inline=True)
        embed.add_field(name="Progress", value=f"`{bar}` {progress*100:.1f}%", inline=False)
        embed.add_field(name="XP in Level", value=f"{xp_in_level}/{total_in_level}", inline=True)
        embed.add_field(name="XP Needed", value=f"{xp_needed} more", inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(RankSystem(bot))
