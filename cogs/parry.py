import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import time
import discord

PARRY_FILE = "data/parry.json"
os.makedirs("data", exist_ok=True)

def load_parry():
    if not os.path.exists(PARRY_FILE):
        return {"total": 0}
    with open(PARRY_FILE, "r") as f:
        return json.load(f)

def save_parry(data):
    with open(PARRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Parry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.parry_data = load_parry()
        self.cooldowns = {}  # user_id: timestamp

    @app_commands.command(name="parry", description="Attempt to parry Gwyn!")
    async def parry(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = time.time()
        last = self.cooldowns.get(int(user_id), 0)
        # 10s cooldown for /parry
        if now - last < 10:
            remaining = int(10 - (now - last))
            await interaction.response.send_message(f"Please wait {remaining}s before parrying again.", ephemeral=True)
            return
        self.cooldowns[int(user_id)] = now

        # Fun parry messages
        messages = [
            "**CLANG!** Gwyn gets parried AGAIN!",
            "*Gwyn attempts a flame sword swing...* \nYou parry it easily!",
            "Gwyn: *\"HRAAA—\"* \nYou press L2.",
            "*Sad piano swells as Gwyn is parried.*",
            "Perfect parry! Gwyn should really learn new moves...",
            "The Lord of Cinder stumbles as you parry his attack!",
            "You parry Gwyn's attack with style and grace!",
            "Gwyn looks confused as you effortlessly parry his strike.",
            "With a swift motion, you parry Gwyn's fiery assault!",
        ]
        msg = random.choice(messages)

        # Ensure parry_data has per-user storage
        if "users" not in self.parry_data:
            self.parry_data["users"] = {}

        # Update total parries and per-user parries
        self.parry_data["total"] = self.parry_data.get("total", 0) + 1
        self.parry_data["users"][user_id] = self.parry_data["users"].get(user_id, 0) + 1
        save_parry(self.parry_data)

        # Build embed
        embed = discord.Embed(
            title=f"{interaction.user.display_name} Parries Gwyn!",
            description=msg,
            color=discord.Color.dark_gold()
        )
        # Show per-user parries from parry_data
        user_parries = self.parry_data.get("users", {}).get(user_id, 0)
        embed.add_field(name="Your Parries", value=user_parries)
        embed.add_field(name="Total Parries", value=self.parry_data["total"])
        # embed.add_field(name="XP Gained", value=xp_gain)
        # embed.add_field(name="Level", value=f"{old_level} → {user['level']}" if user["level"] > old_level else user["level"])
        # embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)

        # Award XP via RankSystem (if loaded)
        rank_cog = self.bot.get_cog("RankSystem")
        if rank_cog:
            xp_gain = random.randint(10, 20)
            try:
                new_level = await rank_cog.award_xp(int(user_id), xp_gain)
                embed.add_field(name="XP Gained", value=f"+{xp_gain}")
                if new_level:
                    embed.add_field(name="Level Up!", value=f"You reached Level {new_level} 🎉")
            except Exception:
                # Don't break parry if rank system fails
                pass

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="parry_reset", description="Reset a user's parry count (admin only)")
    async def parry_reset(self, interaction: discord.Interaction, member: discord.Member):
        # admin check
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Missing permissions (manage_guild).", ephemeral=True)
            return

        user_id = str(member.id)
        if "users" in self.parry_data and user_id in self.parry_data["users"]:
            self.parry_data["users"][user_id] = 0
            save_parry(self.parry_data)
            await interaction.response.send_message(f"Reset parry count for {member.display_name}.")
        else:
            await interaction.response.send_message(f"No parry data for {member.display_name}.")

    @app_commands.command(name="parry_stats", description="Show global parry stats")
    async def parry_stats(self, interaction: discord.Interaction):
        total = self.parry_data.get("total", 0)
        users = self.parry_data.get("users", {})

        embed = discord.Embed(title="Parry Stats", color=discord.Color.dark_gold())
        embed.add_field(name="Total Parries", value=total)

        # Top 5 users
        sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)
        for i, (uid, count) in enumerate(sorted_users[:5], start=1):
            member = interaction.guild.get_member(int(uid)) if interaction.guild else None
            name = member.display_name if member else f"Unknown ({uid})"
            embed.add_field(name=f"#{i} — {name}", value=f"{count} parries", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Parry(bot))
