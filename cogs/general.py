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

    # Slash command: /test — basic healthcheck for interactions
    @app_commands.command(name="test", description="Basic test command to verify slash functionality")
    async def test(self, interaction: discord.Interaction):
        """Simple slash command to confirm the bot receives interactions."""
        try:
            await interaction.response.send_message(f"Test OK — received from {interaction.user.mention}")
        except Exception as e:
            # If the immediate response fails, try to defer then follow up
            print(f"/test handler error: {e}")
            try:
                await interaction.response.defer()
                await interaction.followup.send(f"Test encountered an error: {e}")
            except Exception as e2:
                print(f"/test followup failed: {e2}")

    # Prefix command: !echo text
    @commands.command(name="echo")
    async def echo(self, ctx, *, message: str):
        await ctx.send(message)

    # Prefix command: !ping (checks latency)
    @commands.command(name="ping")
    async def ping_cmd(self, ctx):
        """Responds with bot latency for prefix command usage (!ping)."""
        try:
            latency = round(self.bot.latency * 1000)
            await ctx.send(f"Pong! `{latency} ms`")
        except Exception as e:
            # Keep prefix error handling simple and visible to the caller
            await ctx.send(f"Error: {e}")

    # Error handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(f"Error: {error}")

async def setup(bot):
    await bot.add_cog(General(bot))
