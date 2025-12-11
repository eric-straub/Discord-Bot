"""Info cog — user/server information, avatars, and utility lookups."""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone


class Info(commands.Cog):
    """Information and utility commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Get detailed information about a user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """Show detailed profile info for a member."""
        member = member or interaction.user

        # Calculate account age
        account_age = datetime.now(timezone.utc) - member.created_at
        days = account_age.days
        hours = (account_age.seconds // 3600) % 24

        # Join date
        join_date = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown"

        # Roles
        roles = [role.mention for role in member.roles if role != member.guild.default_role]
        roles_text = ", ".join(roles) if roles else "None"

        # Status
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        status = status_emoji.get(member.status, "❓")

        embed = discord.Embed(
            title=f"User Info — {member.display_name}",
            color=member.color or discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Status", value=f"{status} {member.status.name.capitalize()}", inline=True)
        embed.add_field(name="Account Created", value=f"{days}d {hours}h ago", inline=True)
        embed.add_field(name="Joined Server", value=join_date, inline=True)
        embed.add_field(name="Roles", value=roles_text, inline=False)
        embed.add_field(name="Is Bot", value="Yes" if member.bot else "No", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get information about this server")
    async def serverinfo(self, interaction: discord.Interaction):
        """Show detailed server statistics."""
        guild = interaction.guild

        # Member counts
        total_members = guild.member_count or 0
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots

        # Channel counts
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])

        # Creation date
        created = guild.created_at.strftime("%Y-%m-%d")
        age_days = (datetime.now(timezone.utc) - guild.created_at).days

        # Verification level
        verify_level = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        verification = verify_level.get(guild.verification_level, "Unknown")

        embed = discord.Embed(
            title=f"{guild.name}",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=f"{total_members} ({humans} humans, {bots} bots)", inline=False)
        embed.add_field(name="Channels", value=f"{text_channels} text, {voice_channels} voice, {categories} categories", inline=False)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Created", value=f"{created} ({age_days}d ago)", inline=True)
        embed.add_field(name="Verification Level", value=verification, inline=True)
        embed.add_field(name="Boost Tier", value=f"Level {guild.premium_tier}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar (enlarged)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        """Show a user's avatar in high resolution."""
        member = member or interaction.user

        if not member.avatar:
            await interaction.response.send_message("This user has no avatar.", ephemeral=True)
            return

        avatar_url = member.avatar.url

        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=member.color or discord.Color.blue(),
            url=avatar_url
        )
        embed.set_image(url=avatar_url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="whois", description="Quick lookup of a user or member")
    async def whois(self, interaction: discord.Interaction, *, query: str):
        """Search for a user by name or mention in the current server."""
        # Try to find by mention first
        try:
            member = await commands.MemberConverter().convert(interaction, query)
        except commands.BadArgument:
            # Try to find by name
            members = [m for m in interaction.guild.members if query.lower() in m.display_name.lower()]
            if not members:
                await interaction.response.send_message(f"No members found matching '{query}'.", ephemeral=True)
                return
            if len(members) > 1:
                names = ", ".join([m.mention for m in members[:5]])
                await interaction.response.send_message(f"Multiple matches: {names}", ephemeral=True)
                return
            member = members[0]

        # Reuse userinfo logic
        await self.userinfo(interaction, member)

    @app_commands.command(name="roles", description="List all roles in this server")
    async def roles(self, interaction: discord.Interaction):
        """Display all roles and member counts."""
        guild = interaction.guild
        roles_list = sorted(guild.roles, key=lambda r: r.position, reverse=True)

        embed = discord.Embed(
            title=f"Roles in {guild.name}",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc)
        )

        for role in roles_list[:25]:  # Limit to 25 roles per embed
            member_count = len(role.members)
            embed.add_field(
                name=f"{role.mention}",
                value=f"{member_count} members",
                inline=True
            )

        if len(roles_list) > 25:
            embed.set_footer(text=f"... and {len(roles_list) - 25} more roles")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
