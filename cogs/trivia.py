"""Trivia cog — post questions and reward correct answers with XP and credits."""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import difflib
import re


class Trivia(commands.Cog):
    """Allow users to post trivia questions others can answer for rewards."""

    def __init__(self, bot):
        self.bot = bot
        # active_trivia: channel_id -> trivia dict
        self.active_trivia = {}

    def _normalize_answers(self, raw: str):
        # Accept multiple answers separated by `|` or `,`
        parts = [p.strip().lower() for p in raw.replace('|', ',').split(',') if p.strip()]
        return parts or []

    def _normalize_text(self, s: str) -> str:
        """Lowercase and remove punctuation for matching."""
        s = s or ""
        s = s.lower().strip()
        # keep alphanumeric and spaces
        s = re.sub(r"[^a-z0-9\s]", "", s)
        # collapse whitespace
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def _is_match(self, content: str, answers: list, threshold: float = 0.78) -> bool:
        """Return True if content fuzzily matches any answer.

        Matching strategy (in order): exact match, substring, fuzzy ratio >= threshold.
        """
        if not content:
            return False
        norm_content = self._normalize_text(content)
        for ans in answers:
            norm_ans = self._normalize_text(ans)
            if not norm_ans:
                continue
            if norm_content == norm_ans:
                return True
            if norm_ans in norm_content or norm_content in norm_ans:
                return True
            # fuzzy ratio
            ratio = difflib.SequenceMatcher(None, norm_content, norm_ans).ratio()
            if ratio >= threshold:
                return True
        return False

    def _extract_spoilers(self, content: str) -> list:
        """Return list of strings found inside spoiler tags (||like this||)."""
        if not content:
            return []
        return re.findall(r"\|\|(.+?)\|\|", content, flags=re.DOTALL)

    def _wrap_spoiler(self, s: str) -> str:
        """Wrap a string in spoiler tags, avoiding double-wrapping."""
        if s is None:
            return "||||"
        s = str(s).strip()
        # already wrapped
        if s.startswith("||") and s.endswith("||"):
            return s
        # strip stray pipes then wrap
        inner = s.strip('|')
        return f"||{inner}||"

    async def _end_trivia(self, channel_id: int, reason: str = "time"):
        trivia = self.active_trivia.get(channel_id)
        if not trivia:
            return
        channel = self.bot.get_channel(channel_id)
        if channel:
            revealed = self._wrap_spoiler(trivia.get('answer_display', ''))
            if reason == "time":
                await channel.send(f"⏱️ Trivia ended — no correct answers in time. The answer was: {revealed}")
            elif reason == "cancel":
                await channel.send(f"🛑 Trivia canceled by the asker. The answer was: {revealed}")
        # cleanup
        self.active_trivia.pop(channel_id, None)

    @app_commands.command(name="trivia_post", description="Post a trivia question for others to answer")
    async def trivia_post(self, interaction: discord.Interaction, question: str, answer: str, xp: int = 50, credits: int = 50, duration: int = 10):
        """Post a trivia question. `answer` may include multiple acceptable answers separated by `,` or `|`.

        `xp` and `credits` specify rewards for the first correct answer. `duration` is minutes to wait for an answer.
        """
        await interaction.response.defer()

        channel = interaction.channel
        if not channel:
            await interaction.followup.send("This command must be used in a guild channel.", ephemeral=True)
            return

        if channel.id in self.active_trivia:
            await interaction.followup.send("There's already an active trivia in this channel. Wait for it to finish or cancel it.", ephemeral=True)
            return

        answers = self._normalize_answers(answer)
        if not answers:
            await interaction.followup.send("Provide at least one valid answer.", ephemeral=True)
            return

        trivia = {
            "asker_id": interaction.user.id,
            "question": question,
            "answers": answers,
            "answer_display": answer,
            "xp": max(0, xp),
            "credits": max(0, credits),
            "ends_at": time.time() + max(1, duration) * 60,
            "task": None
        }

        # Announce trivia
        embed = discord.Embed(title="❓ Trivia Time!", color=discord.Color.blurple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Rewards", value=f"{trivia['xp']} XP • {trivia['credits']} credits", inline=True)
        embed.add_field(name="How to answer", value="Reply with your answer inside spoiler tags, e.g. `||your answer||`. Only answers in spoilers will be considered.", inline=False)
        embed.set_footer(text=f"Posted by {interaction.user.display_name} — answers accepted for {duration} minute{'s' if duration != 1 else ''}")

        posted = await channel.send(embed=embed)

        # Store and start timeout watcher
        self.active_trivia[channel.id] = trivia

        async def watcher():
            try:
                remaining = trivia['ends_at'] - time.time()
                if remaining > 0:
                    await asyncio.sleep(remaining)
                # if still active, end due to timeout
                if channel.id in self.active_trivia:
                    await self._end_trivia(channel.id, reason="time")
            except asyncio.CancelledError:
                return

        task = self.bot.loop.create_task(watcher())
        trivia['task'] = task

        await interaction.followup.send(f"Posted trivia in {channel.mention}")

    @app_commands.command(name="trivia_cancel", description="Cancel the active trivia in this channel")
    async def trivia_cancel(self, interaction: discord.Interaction):
        """Cancel an active trivia. Only the asker or admins can cancel."""
        channel = interaction.channel
        if not channel or channel.id not in self.active_trivia:
            await interaction.response.send_message("No active trivia in this channel.", ephemeral=True)
            return

        trivia = self.active_trivia[channel.id]
        is_asker = trivia.get('asker_id') == interaction.user.id
        if not is_asker and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("Only the asker or staff can cancel the trivia.", ephemeral=True)
            return

        # cancel background task
        task = trivia.get('task')
        if task and not task.done():
            task.cancel()

        await self._end_trivia(channel.id, reason="cancel")
        await interaction.response.send_message("Trivia canceled.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Listen for answers in channels with active trivia
        if message.author.bot:
            return
        channel = message.channel
        trivia = self.active_trivia.get(channel.id)
        if not trivia:
            return

        # Extract content from spoiler tags only
        spoilers = self._extract_spoilers(message.content)
        if not spoilers:
            return
        
        # Check if any spoiler content matches the answer
        matched = False
        for spoiler_content in spoilers:
            if self._is_match(spoiler_content, trivia['answers']):
                matched = True
                break
        
        if matched:
            # first correct answer wins
            asker_id = trivia.get('asker_id')
            if message.author.id == asker_id:
                await channel.send(f"Nice try {message.author.mention}, the asker cannot answer their own trivia.")
                return

            # award XP and credits via other cogs if available
            awarded_xp = trivia.get('xp', 0)
            awarded_credits = trivia.get('credits', 0)

            rank_cog = self.bot.get_cog('RankSystem')
            econ_cog = self.bot.get_cog('Economy')

            level_up_msg = None
            if rank_cog:
                try:
                    new_level = await rank_cog.award_xp(message.author.id, awarded_xp)
                    if new_level:
                        level_up_msg = f" They leveled up to Level {new_level}! 🎉"
                except Exception as e:
                    print(f"Error awarding XP: {e}")

            if econ_cog:
                try:
                    econ_cog._add_balance(message.author.id, awarded_credits)
                except Exception as e:
                    print(f"Error awarding credits: {e}")

            await channel.send(f"✅ Correct! {message.author.mention} answered correctly and wins {awarded_xp} XP and {awarded_credits} credits.{level_up_msg or ''}")

            # cleanup: cancel watcher and remove active trivia
            task = trivia.get('task')
            if task and not task.done():
                task.cancel()
            self.active_trivia.pop(channel.id, None)

    @commands.command(name="trivia_post")
    async def trivia_post_prefix(self, ctx, question: str, answer: str, xp: int = 50, credits: int = 50, duration: int = 10):
        """Prefix wrapper: !trivia_post <question> <answer> [xp] [credits] [duration_minutes]
        Note: space-separated args may be awkward; prefer using slash command.
        """
        # Provide a simple compatibility wrapper that forwards to the slash handler
        await ctx.send("Please use the slash command `/trivia_post` in modern clients."
                       " This prefix wrapper exists but has limited parsing.")


async def setup(bot):
    await bot.add_cog(Trivia(bot))
