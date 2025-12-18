import discord
from discord.ext import commands
from discord import app_commands
import subprocess
from datetime import datetime, timezone


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        """Check bot's response time in milliseconds."""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! `{latency} ms`")

    @app_commands.command(name="hello", description="The bot says hello")
    async def hello(self, interaction: discord.Interaction):
        """Friendly greeting command."""
        await interaction.response.send_message(f"Hello, {interaction.user.mention}! 👋")

    @app_commands.command(name="echo", description="Make the bot repeat your message")
    @app_commands.describe(message="The message to repeat")
    async def echo(self, interaction: discord.Interaction, message: str):
        """Repeat the user's message."""
        await interaction.response.send_message(message)

    @commands.command(name="ping")
    async def ping_cmd(self, ctx):
        """Prefix command version of ping."""
        try:
            latency = round(self.bot.latency * 1000)
            await ctx.send(f"Pong! `{latency} ms`")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @app_commands.command(name="version", description="Show bot version and info")
    async def version(self, interaction: discord.Interaction):
        """Display bot version information."""
        version = getattr(self.bot, 'version', 'Unknown')
        
        embed = discord.Embed(
            title="Discord Bot Version",
            description=f"**Version:** `{version}`",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="Alpha Release", inline=True)
        embed.add_field(name="Discord.py", value=f"`{discord.__version__}`", inline=True)
        
        # Get last git commit timestamp
        try:
            # Get timestamp of last commit
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ct'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                commit_timestamp = int(result.stdout.strip())
                commit_dt = datetime.fromtimestamp(commit_timestamp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                
                # Calculate time difference
                delta = now - commit_dt
                
                # Format time ago
                if delta.days > 0:
                    if delta.days == 1:
                        time_ago = "1 day ago"
                    else:
                        time_ago = f"{delta.days} days ago"
                else:
                    hours = delta.seconds // 3600
                    minutes = (delta.seconds % 3600) // 60
                    
                    if hours > 0:
                        if hours == 1:
                            time_ago = "1 hour ago"
                        else:
                            time_ago = f"{hours} hours ago"
                    elif minutes > 0:
                        if minutes == 1:
                            time_ago = "1 minute ago"
                        else:
                            time_ago = f"{minutes} minutes ago"
                    else:
                        time_ago = "Just now"
                
                embed.add_field(name="Last Update", value=time_ago, inline=False)
        except Exception as e:
            print(f"[version] Failed to get git info: {e}")
            # Silently ignore git errors - command still works without this field
        
        embed.set_footer(text="Discord Bot by Eric Straub")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="server_stats", description="Show basic server statistics")
    async def server_stats(self, interaction: discord.Interaction):
        """Display comprehensive server statistics."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server (guild).", ephemeral=True)
            return

        total = guild.member_count
        bots = sum(1 for m in guild.members if m.bot)
        humans = total - bots
        online = sum(1 for m in guild.members if getattr(m, "status", discord.Status.offline) != discord.Status.offline)
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        roles = len(guild.roles)
        owner = guild.owner

        embed = discord.Embed(title=f"{guild.name} — Server Stats", color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Total Members", value=str(total))
        embed.add_field(name="Humans", value=str(humans))
        embed.add_field(name="Bots", value=str(bots))
        embed.add_field(name="Online (approx)", value=str(online))
        embed.add_field(name="Text Channels", value=str(text_channels))
        embed.add_field(name="Voice Channels", value=str(voice_channels))
        embed.add_field(name="Roles", value=str(roles))
        embed.add_field(name="Owner", value=owner.mention if owner else "Unknown")
        embed.set_footer(text=f"Created: {guild.created_at.date()}")

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Log interactions for debugging purposes."""
        try:
            name = None
            if hasattr(interaction, "data") and interaction.data:
                name = interaction.data.get("name") if isinstance(interaction.data, dict) else None
            print(f"[interaction] id={interaction.id} user={interaction.user} name={name} type={interaction.type}")
        except Exception as e:
            print(f"[interaction] Logging failed: {e}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors for prefix commands."""
        await ctx.send(f"Error: {error}")

    def _build_help_embed(self, category: str = None, *, author: discord.abc.User = None) -> discord.Embed:
        """Construct a help embed with command categories and examples."""
        categories_desc = {
            "general": "General utility commands (ping, hello, server stats)",
            "rank": "Rank and XP system (rank, leaderboard, profile)",
            "fun": "Fun and games (dice, coin, rock-paper-scissors, 8ball)",
            "games": "Interactive games (pong, snake, game of life)",
            "moderation": "Moderation tools (warn, timeout, purge)",
            "economy": "Currency and wallet system (balance, pay, daily)",
            "trivia": "Interactive trivia questions with rewards",
            "casino": "Gambling games (blackjack, slots, roulette, coinflip, dice, crash)",
            "settings": "Server configuration (prefix, XP toggle, autorole)"
        }

        examples = {
            "general": "`/ping`, `/hello`, `/version`, `/server_stats`",
            "rank": "`/rank`, `/leaderboard`, `/next_level`",
            "fun": "`/dice 2d20`, `/coin`, `/rps rock`, `/8ball <question>`",
            "games": "`/pong`, `/snake`, `/gameoflife`",
            "moderation": "`/warn <user>`, `/timeout <user> 1h`, `/purge 5`",
            "economy": "`/balance`, `/daily`, `/pay <user> 50`",
            "trivia": "`/trivia_post <question> <answer>`",
            "casino": "`/blackjack <bet>`, `/slots <bet>`, `/roulette <bet> <choice>`, `/coinflip <bet> <choice>`, `/dice <bet> <choice>`, `/crash <bet>`",
            "settings": "`/config_show`, `/config_prefix !`"
        }

        title = "📚 Help & Command Guide"
        description = (
            "I'm a multipurpose Discord bot with XP tracking, economy, moderation, games, and more! "
            "Use slash commands like `/ping` or prefix commands like `!ping`."
        )

        embed = discord.Embed(title=title, color=discord.Color.blurple(), description=description)

        if not category:
            # Show all categories
            embed.add_field(
                name="How to Use",
                value="Type `/` to see slash commands, or use `!` for prefix commands. Use `/help <category>` for details.",
                inline=False
            )
            for cat, desc in sorted(categories_desc.items()):
                embed.add_field(name=cat.capitalize(), value=desc, inline=False)
            embed.set_footer(text="Type /help <category> for examples")
        else:
            # Show specific category
            cat = category.lower()
            if cat not in categories_desc:
                embed = discord.Embed(
                    title="Unknown Category",
                    color=discord.Color.red(),
                    description=f"Available categories: {', '.join(sorted(categories_desc.keys()))}"
                )
                return embed

            embed.title = f"📚 Help — {cat.capitalize()} Commands"
            embed.description = categories_desc[cat]
            embed.add_field(name="Examples", value=examples.get(cat, "No examples available"), inline=False)
            embed.set_footer(text="Use /help to see all categories")

        if author:
            embed.set_author(name=f"Requested by {author.display_name}", icon_url=author.avatar.url if author.avatar else None)

        return embed

    @app_commands.command(name="help", description="Show available commands and categories")
    async def help(self, interaction: discord.Interaction, category: str = None):
        """Display bot commands organized by category."""
        embed = self._build_help_embed(category, author=interaction.user)
        await interaction.response.send_message(embed=embed)

    @commands.command(name="help")
    async def help_cmd(self, ctx, *, category: str = None):
        """Prefix command version of help."""
        embed = self._build_help_embed(category, author=ctx.author)
        await ctx.send(embed=embed)


async def setup(bot):
    general = General(bot)
    bot.start_time = __import__('time').time()  # Track bot start time
    await bot.add_cog(general)
