"""Trivia cog — post questions and reward correct answers with XP and credits."""

import asyncio
import time
import difflib
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands


class Trivia(commands.Cog):
    """Allow users to post trivia questions others can answer for rewards."""

    def __init__(self, bot):
        self.bot = bot
        # active_trivia: channel_id -> trivia dict
        self.active_trivia = {}
        # pending_trivia: user_id -> {question, channel_id, message}
        self.pending_trivia = {}

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

    async def _handle_trivia_mention(self, message: discord.Message):
        """Handle when someone mentions @Daily Trivia to create a trivia question."""
        channel = message.channel
        
        # Check if channel supports sending messages
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return
        
        # Check if there's already active trivia in this channel
        if channel.id in self.active_trivia:
            try:
                await message.add_reaction("⏸️")  # Pause/wait emoji
            except Exception:
                pass
            return
        
        # Extract question and answer from the message
        content = message.content
        
        # Remove the @Daily Trivia mention
        content = re.sub(r"@Daily Trivia", "", content, flags=re.IGNORECASE).strip()
        
        # Extract spoilers (these are the answers)
        spoilers = self._extract_spoilers(content)
        if not spoilers:
            # No answer provided - DM the user to ask for it
            question = content.strip()
            if not question:
                try:
                    await message.add_reaction("❓")  # No question found
                except Exception:
                    pass
                return
            
            # Store pending trivia
            self.pending_trivia[message.author.id] = {
                "question": question,
                "channel_id": channel.id,
                "message": message
            }
            
            # DM the user
            try:
                await message.author.send(
                    f"❓ You posted a trivia question but didn't include an answer in spoiler tags.\n\n"
                    f"**Question:** {question}\n\n"
                    f"Please reply to this DM with the answer in spoiler tags, e.g., `||your answer||`"
                )
                await message.add_reaction("📬")  # Mailbox emoji to indicate DM sent
            except discord.Forbidden:
                try:
                    await message.add_reaction("🔒")  # Can't DM user
                except Exception:
                    pass
            except Exception as e:
                print(f"Error sending DM: {e}")
                try:
                    await message.add_reaction("❓")
                except Exception:
                    pass
            return
        
        # The first spoiler is the answer
        answer_text = spoilers[0]
        
        # Remove spoiler tags from content to get the question
        question = re.sub(r"\|\|.+?\|\|", "", content, flags=re.DOTALL).strip()
        
        if not question:
            try:
                await message.add_reaction("❓")  # No question found
            except Exception:
                pass
            return
        
        # Parse the answer for multiple acceptable answers
        answers = self._normalize_answers(answer_text)
        if not answers:
            try:
                await message.add_reaction("❓")
            except Exception:
                pass
            return
        
        # Calculate end time: 6am the next day
        now = datetime.now()
        
        # Get tomorrow's date
        tomorrow = now.date() + timedelta(days=1)
        
        # Set end time to 6am tomorrow
        next_6am = datetime.combine(tomorrow, datetime.min.time()).replace(hour=6)
        
        # Convert to Unix timestamp
        ends_at = next_6am.timestamp()
        
        # Default rewards
        xp = 50
        credits = 50
        
        trivia = {
            "asker_id": message.author.id,
            "question": question,
            "answers": answers,
            "answer_display": answer_text,
            "xp": xp,
            "credits": credits,
            "ends_at": ends_at,
            "task": None,
            "correct_users": []
        }
        
        # Store trivia
        self.active_trivia[channel.id] = trivia
        
        # Start timeout watcher
        async def watcher():
            try:
                remaining = trivia['ends_at'] - time.time()
                if remaining > 0:
                    await asyncio.sleep(remaining)
                if channel.id in self.active_trivia:
                    await self._end_trivia(channel.id, reason="time")
            except asyncio.CancelledError:
                return
        
        task = self.bot.loop.create_task(watcher())
        trivia['task'] = task
        
        # Add checkmark reaction to confirm trivia was created
        try:
            await message.add_reaction("✅")
        except Exception:
            pass

    async def _handle_trivia_answer_dm(self, message: discord.Message):
        """Handle DM reply with trivia answer."""
        user_id = message.author.id
        pending = self.pending_trivia.get(user_id)
        if not pending:
            return
        
        # Extract spoilers from DM
        spoilers = self._extract_spoilers(message.content)
        if not spoilers:
            try:
                await message.channel.send(
                    "❓ Please provide the answer in spoiler tags, e.g., `||your answer||`"
                )
            except Exception:
                pass
            return
        
        # Get the answer
        answer_text = spoilers[0]
        answers = self._normalize_answers(answer_text)
        if not answers:
            try:
                await message.channel.send(
                    "❓ Invalid answer format. Please try again with spoiler tags, e.g., `||your answer||`"
                )
            except Exception:
                pass
            return
        
        # Get the channel where trivia was posted
        channel = self.bot.get_channel(pending["channel_id"])
        if not channel:
            try:
                await message.channel.send("❌ Could not find the original channel. Trivia canceled.")
            except Exception:
                pass
            self.pending_trivia.pop(user_id, None)
            return
        
        # Check if there's already active trivia in that channel
        if channel.id in self.active_trivia:
            try:
                await message.channel.send(
                    "⏸️ There's already an active trivia in that channel. Your question was not posted."
                )
            except Exception:
                pass
            self.pending_trivia.pop(user_id, None)
            return
        
        # Calculate end time: 6am the next day
        now = datetime.now()
        tomorrow = now.date() + timedelta(days=1)
        next_6am = datetime.combine(tomorrow, datetime.min.time()).replace(hour=6)
        ends_at = next_6am.timestamp()
        
        # Default rewards
        xp = 50
        credits = 50
        
        trivia = {
            "asker_id": user_id,
            "question": pending["question"],
            "answers": answers,
            "answer_display": answer_text,
            "xp": xp,
            "credits": credits,
            "ends_at": ends_at,
            "task": None,
            "correct_users": []
        }
        
        # Store trivia
        self.active_trivia[channel.id] = trivia
        
        # Start timeout watcher
        async def watcher():
            try:
                remaining = trivia['ends_at'] - time.time()
                if remaining > 0:
                    await asyncio.sleep(remaining)
                if channel.id in self.active_trivia:
                    await self._end_trivia(channel.id, reason="time")
            except asyncio.CancelledError:
                return
        
        task = self.bot.loop.create_task(watcher())
        trivia['task'] = task
        
        # React to original message
        original_msg = pending.get("message")
        if original_msg:
            try:
                await original_msg.add_reaction("✅")
            except Exception:
                pass
        
        # Confirm to user via DM
        try:
            await message.channel.send(
                f"✅ Trivia question posted! It will remain active until 6am tomorrow."
            )
        except Exception:
            pass
        
        # Remove from pending
        self.pending_trivia.pop(user_id, None)



    async def _end_trivia(self, channel_id: int, reason: str = "time"):
        trivia = self.active_trivia.get(channel_id)
        if not trivia:
            return
        channel = self.bot.get_channel(channel_id)
        if channel:
            revealed = self._wrap_spoiler(trivia.get('answer_display', ''))
            correct_users = trivia.get('correct_users', [])
            if reason == "time":
                if correct_users:
                    user_mentions = ", ".join([f"<@{uid}>" for uid in correct_users])
                    await channel.send(f"⏱️ Trivia ended! The answer was: {revealed}\n✅ Correct answerers: {user_mentions}")
                else:
                    await channel.send(f"⏱️ Trivia ended — no correct answers in time. The answer was: {revealed}")
            elif reason == "cancel":
                await channel.send(f"🛑 Trivia canceled by the asker. The answer was: {revealed}")
        # cleanup
        self.active_trivia.pop(channel_id, None)

    @app_commands.command(name="trivia_post", description="Post a trivia question for others to answer")
    @app_commands.checks.cooldown(1, 30.0)  # 1 use per 30 seconds
    async def trivia_post(self, interaction: discord.Interaction, question: str, answer: str, xp: int = 50, credits: int = 50, duration: int = 10):
        """Post a trivia question. `answer` may include multiple acceptable answers separated by `,` or `|`.

        `xp` and `credits` specify rewards for the first correct answer. `duration` is minutes to wait for an answer.
        """
        await interaction.response.defer()

        channel = interaction.channel
        if not channel:
            await interaction.followup.send("This command must be used in a guild channel.", ephemeral=True)
            return

        # Check if channel supports sending messages
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            await interaction.followup.send("This command can only be used in text channels or threads.", ephemeral=True)
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
            "task": None,
            "correct_users": []  # Track all users who answered correctly
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

    @trivia_post.error
    async def trivia_post_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for the trivia_post command, especially cooldowns."""
        if isinstance(error, app_commands.CommandOnCooldown):
            # Convert seconds to a human-readable format
            remaining = int(error.retry_after)
            await interaction.response.send_message(
                f"⏱️ This command is on cooldown. Please wait **{remaining} seconds** before posting another trivia question.",
                ephemeral=True
            )
        else:
            # Re-raise other errors for the default error handler
            raise error

    @app_commands.command(name="trivia_cancel", description="Cancel the active trivia in this channel")
    async def trivia_cancel(self, interaction: discord.Interaction):
        """Cancel an active trivia. Only the asker or admins can cancel."""
        channel = interaction.channel
        if not channel or channel.id not in self.active_trivia:
            await interaction.response.send_message("No active trivia in this channel.", ephemeral=True)
            return

        trivia = self.active_trivia[channel.id]
        is_asker = trivia.get('asker_id') == interaction.user.id
        is_staff = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.manage_guild
        if not is_asker and not is_staff:
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
        
        # Check if this is a DM with a pending trivia answer
        if isinstance(channel, discord.DMChannel) and message.author.id in self.pending_trivia:
            await self._handle_trivia_answer_dm(message)
            return
        
        # Check if message mentions @Daily Trivia to create a new trivia question
        if "@Daily Trivia" in message.content or "@daily trivia" in message.content.lower():
            await self._handle_trivia_mention(message)
            return
        
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
            # Allow multiple users to answer correctly
            asker_id = trivia.get('asker_id')
            if message.author.id == asker_id:
                try:
                    await message.add_reaction("❌")
                except Exception:
                    pass
                return

            # Check if this user already answered correctly
            correct_users = trivia.get('correct_users', [])
            if message.author.id in correct_users:
                await message.add_reaction("✅")  # Silent acknowledgment
                return

            # Add user to correct answerers list
            correct_users.append(message.author.id)
            trivia['correct_users'] = correct_users

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

            try:
                await message.add_reaction("✅")
            except Exception:
                pass

            # Trivia continues until time expires (don't cancel task or remove trivia)


async def setup(bot):
    await bot.add_cog(Trivia(bot))
