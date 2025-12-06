import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from cogs.rank import RANK_FILE, calculate_level, load_ranks, save_ranks

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
        self.ranks = load_ranks()  # for per-user parry stats

    @app_commands.command(name="parry", description="Attempt to parry Gwyn!")
    async def parry(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Fun parry messages
        messages = [
            "**CLANG!** Gwyn gets parried AGAIN!",
            "*Gwyn attempts a flame sword swing...* \nYou: **No.** *Parry.*",
            "Gwyn: *\"HRAAA—\"* \nYou: **\"Sit down.\"** *Parry.*",
            "*Sad piano intensifies as Gwyn is parried.*",
            "Perfect parry! Gwyn should really learn new moves.",
        ]
        msg = random.choice(messages)

        # Update total parries
        self.parry_data["total"] = self.parry_data.get("total", 0) + 1
        save_parry(self.parry_data)

        # Update per-user XP and parries
        if user_id not in self.ranks:
            self.ranks[user_id] = {"xp": 0, "level": 0, "parries": 0}
        user = self.ranks[user_id]
        user["parries"] = user.get("parries", 0) + 1

        # Give XP for parrying
        xp_gain = random.randint(20, 40)
        user["xp"] += xp_gain
        old_level = user["level"]
        user["level"] = calculate_level(user["xp"])
        save_ranks(self.ranks)

        # Build embed
        embed = discord.Embed(
            title=f"{interaction.user.display_name} Parries Gwyn!",
            description=msg,
            color=discord.Color.dark_gold()
        )
        embed.add_field(name="Your Parries", value=user["parries"])
        embed.add_field(name="Total Parries", value=self.parry_data["total"])
        # embed.add_field(name="XP Gained", value=xp_gain)
        # embed.add_field(name="Level", value=f"{old_level} → {user['level']}" if user["level"] > old_level else user["level"])
        # embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Parry(bot))
