"""Fun and games cog — dice rolls, coin flips, rock-paper-scissors, and more."""

import random

import discord
from discord.ext import commands
from discord import app_commands


class Fun(commands.Cog):
    """Fun commands for entertainment."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dice", description="Roll a d20 or custom dice (e.g., 2d6)")
    @app_commands.checks.cooldown(1, 3.0)  # 1 use per 3 seconds
    async def dice(self, interaction: discord.Interaction, dice: str = "d20"):
        """Roll dice. Format: NdX (e.g., 2d6, 3d20). Defaults to d20."""
        try:
            if "d" not in dice.lower():
                await interaction.response.send_message("Invalid format. Use NdX (e.g., 2d6, d20).", ephemeral=True)
                return

            parts = dice.lower().split("d")
            num_dice = int(parts[0]) if parts[0] else 1
            sides = int(parts[1])

            if num_dice < 1 or num_dice > 100 or sides < 1 or sides > 1000:
                await interaction.response.send_message("Keep it reasonable: 1-100 dice, 1-1000 sides.", ephemeral=True)
                return

            rolls = [random.randint(1, sides) for _ in range(num_dice)]
            total = sum(rolls)

            result = f"🎲 **{interaction.user.display_name}** rolled `{dice}`\n"
            if num_dice <= 10:
                result += f"Rolls: {', '.join(map(str, rolls))}\n"
            result += f"**Total: {total}**"

            await interaction.response.send_message(result)
        except ValueError:
            await interaction.response.send_message("Invalid format. Use NdX (e.g., 2d6, d20).", ephemeral=True)

    @app_commands.command(name="coin", description="Flip a coin")
    @app_commands.checks.cooldown(1, 3.0)  # 1 use per 3 seconds
    async def coin(self, interaction: discord.Interaction):
        """Flip a fair coin."""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"
        await interaction.response.send_message(f"{emoji} **{result}!**")

    @app_commands.command(name="rps", description="Play rock-paper-scissors")
    @app_commands.checks.cooldown(1, 3.0)  # 1 use per 3 seconds
    async def rps(self, interaction: discord.Interaction, choice: str):
        """Play rock-paper-scissors. Choices: rock, paper, scissors."""
        choices = ["rock", "paper", "scissors"]
        if choice.lower() not in choices:
            await interaction.response.send_message(f"Choose: {', '.join(choices)}", ephemeral=True)
            return

        bot_choice = random.choice(choices)
        user_choice = choice.lower()

        # Determine outcome
        if user_choice == bot_choice:
            outcome = "It's a tie! 🤝"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "scissors" and bot_choice == "paper") or \
             (user_choice == "paper" and bot_choice == "rock"):
            outcome = "You win! 🎉"
        else:
            outcome = "I win! 🤖"

        embed = discord.Embed(title="Rock-Paper-Scissors", color=discord.Color.blue())
        embed.add_field(name="Your Choice", value=user_choice.capitalize(), inline=True)
        embed.add_field(name="My Choice", value=bot_choice.capitalize(), inline=True)
        embed.add_field(name="Result", value=outcome, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a yes/no question")
    @app_commands.checks.cooldown(1, 5.0)  # 1 use per 5 seconds
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Consult the magic 8-ball for wisdom."""
        responses = [
            "Yes, definitely.", "It is certain.", "Most likely.", "Outlook good.",
            "Maybe.", "Ask again later.", "Cannot predict now.", "Unclear.",
            "No, absolutely not.", "Outlook not so good.", "Don't count on it.", "Definitely not."
        ]
        response = random.choice(responses)
        await interaction.response.send_message(f"🔮 *{response}*")

    @app_commands.command(name="choose", description="Randomly choose from a list")
    async def choose(self, interaction: discord.Interaction, *, options: str):
        """Choose randomly from comma-separated options (e.g., pizza, tacos, sushi)."""
        choices = [opt.strip() for opt in options.split(",")]
        if len(choices) < 2:
            await interaction.response.send_message("Provide at least 2 options separated by commas.", ephemeral=True)
            return

        choice = random.choice(choices)
        await interaction.response.send_message(f"🎯 I choose: **{choice}**")


async def setup(bot):
    await bot.add_cog(Fun(bot))
