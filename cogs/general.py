import discord
from discord.ext import commands
from discord import app_commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command: /ping
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! `{latency} ms`")

    # Slash command: /hello
    @app_commands.command(name="hello", description="The bot says hello")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hello, {interaction.user.mention}! 👋")

    # Prefix command: !echo text
    @commands.command(name="echo")
    async def echo(self, ctx, *, message: str):
        await ctx.send(message)

    # Prefix command: !ping
    @commands.command(name="ping")
    async def ping(self, ctx, *):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! `{latency} ms`")

    # Error handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(f"Error: {error}")

async def setup(bot):
    await bot.add_cog(General(bot))
