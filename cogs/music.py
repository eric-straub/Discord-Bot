import asyncio
import functools
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import os

# YTDL and FFmpeg options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'extract_flat': False,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource:
    def __init__(self, data, requester):
        self.data = data
        self.requester = requester
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        # direct audio url (may be None when using ffmpeg to read webpage)
        self.url = data.get('url')

    @classmethod
    async def create(cls, search: str, loop=None, requester=None):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        except Exception as e:
            msg = str(e)
            # Detect common yt-dlp message when YouTube requests login/cookies
            if "Sign in to confirm you\u2019re not a bot" in msg or "use --cookies" in msg.lower() or "cookies-from-browser" in msg.lower():
                raise RuntimeError(
                    "yt-dlp failed: YouTube is requesting authentication/cookies. "
                    "Export browser cookies or use yt-dlp's --cookies-from-browser option. "
                    "See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
                ) from e
            # propagate other errors
            raise

        # ytdl.extract_info returns dict for single or playlist
        if 'entries' in data:
            # take first entry
            entry = data['entries'][0]
        else:
            entry = data

        # If entry contains formats, pick the url for ffmpeg to use
        return cls(entry, requester)


class MusicPlayer:
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.current = None
        self.volume = 0.5
        self.audio_player = bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        while True:
            self.next.clear()
            # get next source
            source = await self.queue.get()
            self.current = source

            voice = self.guild.voice_client
            if voice is None:
                # attempt to reconnect if possible
                self.current = None
                continue

            ffmpeg_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source.web_url or source.data.get('url'), **ffmpeg_options), volume=self.volume)
            voice.play(ffmpeg_source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.next.set))

            await self.next.wait()
            # loop will continue to next track

    def add_to_queue(self, source: YTDLSource):
        self.queue.put_nowait(source)

    def skip(self):
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()

    def pause(self):
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()

    def resume(self):
        vc = self.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(2.0, vol))


class Music(commands.Cog):
    """Music cog: play audio from YouTube using yt-dlp and FFmpeg."""

    def __init__(self, bot):
        self.bot = bot
        self.players = {}  # guild_id -> MusicPlayer

    def get_player(self, guild: discord.Guild) -> MusicPlayer:
        player = self.players.get(guild.id)
        if not player:
            player = MusicPlayer(self.bot, guild)
            self.players[guild.id] = player
        return player

    async def ensure_voice(self, interaction: discord.Interaction):
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            await interaction.response.send_message("You must be in a voice channel to use music commands.", ephemeral=True)
            return None

        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if vc is None:
            try:
                vc = await channel.connect()
            except Exception as e:
                await interaction.response.send_message(f"Failed to join voice channel: {e}", ephemeral=True)
                return None
        else:
            if vc.channel.id != channel.id:
                await vc.move_to(channel)

        return vc

    @app_commands.command(name="play", description="Play a YouTube URL or search term")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        vc = await self.ensure_voice(interaction)
        if vc is None:
            return

        # create source
        try:
            source = await YTDLSource.create(query, loop=self.bot.loop, requester=interaction.user)
        except Exception as e:
            await interaction.followup.send(f"Error processing this request: {e}")
            return

        player = self.get_player(interaction.guild)
        player.add_to_queue(source)

        await interaction.followup.send(f"Queued: **{source.title}**")

    @app_commands.command(name="skip", description="Skip current track")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("Not connected to a voice channel.", ephemeral=True)
            return
        player = self.get_player(interaction.guild)
        player.skip()
        await interaction.response.send_message("Skipped.")

    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return
        vc.pause()
        await interaction.response.send_message("Paused.")

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("Not connected to a voice channel.", ephemeral=True)
            return
        vc.resume()
        await interaction.response.send_message("Resumed.")

    @app_commands.command(name="queue", description="Show current queue")
    async def queue(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild)
        q = list(player.queue._queue)
        if not q:
            await interaction.response.send_message("Queue is empty.")
            return
        lines = [f"{i+1}. {item.title}" for i, item in enumerate(q)]
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="now", description="Show now playing")
    async def now(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild)
        if not player.current:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return
        await interaction.response.send_message(f"Now playing: **{player.current.title}**")

    @app_commands.command(name="volume", description="Set playback volume (0.0-2.0)")
    async def volume(self, interaction: discord.Interaction, vol: float):
        player = self.get_player(interaction.guild)
        player.set_volume(vol)
        # try to adjust current source's volume transformer
        vc = interaction.guild.voice_client
        if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = player.volume
        await interaction.response.send_message(f"Volume set to {player.volume}")

    @app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("Not connected to a voice channel.", ephemeral=True)
            return
        player = self.get_player(interaction.guild)
        # clear queue
        while not player.queue.empty():
            try:
                player.queue.get_nowait()
            except Exception:
                break
        if vc.is_playing():
            vc.stop()
        await interaction.response.send_message("Stopped playback and cleared queue.")

async def setup(bot):
    await bot.add_cog(Music(bot))
