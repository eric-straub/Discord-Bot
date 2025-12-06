import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random

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

    @app_commands.command(name="parry", description="Attempt to parry Gwyn!")
    async def parry(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

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

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Parry(bot))
