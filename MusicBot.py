import os
import re
import time
import yt_dlp
import discord
import collections
from discord.ext import commands
from dataclasses import dataclass
from ControlView import SerenadikView


FFMPEG_OPTIONS = {'options': '-vn', 
                  'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}
YDL_OPTIONS = {'format': 'bestaudio'}
YDL_OPTIONS_EXT = {
    'extract_flat': 'in_playlist',  
    'skip_download': True,          
    'quiet': True                   
}
URL_REGEX = re.compile(r'(https?:\\/\\/)?(?:www\\.)?(youtube|youtu|youtube-nocookie|music.youtube)\.(com|be)/.+')
BLACKLIST_FILE = "blacklist"

class SerenadikBot(commands.Cog):

    @dataclass
    class _SongInfo:
        url: str
        title: str
        duration: str
        thumbnail: str
        link: str

    _blacklisted_users = set()

    def __init__(self, client):
        self.client = client
        self.queues = {}
        self.looped_songs = {}
        self.history_queues = {}
        self.songs_start_time = {}
        self.manually_stopped_flags = {}
        self.ydl = yt_dlp.YoutubeDL(YDL_OPTIONS)
        self.client.add_check(self.__globally_block)
        self.ydl_ext = yt_dlp.YoutubeDL(YDL_OPTIONS_EXT)

        SerenadikBot._blacklisted_users = SerenadikBot.__load_blacklist()

    def __load_blacklist():
         with open(BLACKLIST_FILE, 'a+') as file:
             file.seek(0)
             return set(line.strip() for line in file)

    def __save_blacklist():
        with open(BLACKLIST_FILE, 'w') as file:
            for user_id in SerenadikBot._blacklisted_users:
                file.write(f"{ user_id }\n")

    def ban_user(user_id: str):
        SerenadikBot._blacklisted_users.add(user_id)
        SerenadikBot.__save_blacklist()
    
    def unban_user(user_id: str):
        SerenadikBot._blacklisted_users.discard(user_id)
        SerenadikBot.__save_blacklist()

    async def __globally_block(self, ctx):
        if str(ctx.author.id) in SerenadikBot._blacklisted_users:
            await ctx.send("❀◕ ‿ ◕❀ The bot owner has banned you from using any commands")
            return False
        return True
    
    def get_queues(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = collections.deque()
            self.history_queues[guild_id] = []
        return (self.queues[guild_id], self.history_queues[guild_id])

    def __get_looped_song(self, guild_id):
        if guild_id not in self.looped_songs:
            self.looped_songs[guild_id] = None
        return self.looped_songs[guild_id]

    def __get_manually_stopped(self, guild_id):
        if guild_id not in self.manually_stopped_flags:
            self.manually_stopped_flags[guild_id] = False
        return self.manually_stopped_flags[guild_id]

    def __get_current_playback_time(self, guild_id):
        if guild_id not in self.songs_start_time:
            return 0
        
        elapsed = max(0, time.time() - self.songs_start_time[guild_id])
        return int(elapsed)

    def __extract_song_info(self, url, search=False):
        if search:
            url = f"ytsearch:{url}"
        
        info = self.ydl.extract_info(url, download=False)

        if search and 'entries' in info:
            info = info['entries'][0]

        return self._SongInfo(
            info['url'], 
            info['title'], 
            info['duration'], 
            info['thumbnail'], 
            info['webpage_url']
        )

    async def __add_playlist_to_queue(self, ctx, url, queue, force=False):
        try:
            playlist_info = self.ydl_ext.extract_info(url, download=False)
            total_songs = len(playlist_info['entries'])
            playlist_title = playlist_info.get('title', 'Mix Youtube') 
            playlist_entries = playlist_info['entries']
            append_method = queue.append

            if force:
                playlist_entries = reversed(playlist_entries)
                append_method = queue.appendleft

            for entry in playlist_entries:
                append_method(entry['url'])

            embed = discord.Embed(
                title=f" (♡μ_μ) **PLaylist added { "to the top" if force else "to the end" }** :inbox_tray:",
                description=f"Title: **[{playlist_title}]({url})**\n Song count: **{total_songs}**",
                color=discord.Color.blue()
            )
            
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error processing playlist: {e}")

    async def __add_song_to_queue(self, ctx, url, queue, is_link=True, force=False):
        song_info = self.__extract_song_info(url, not is_link)
        queue.appendleft(song_info) if force else queue.append(song_info)

        embed = discord.Embed(
            title=f" (♡μ_μ) **Song added { "to the top" if force else "to the end" }** :inbox_tray:",
            description=f"Title: **[{song_info.title}]({song_info.link})**",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    async def __add_to_queue(self, ctx, url, force=False):
        queue, _ = self.get_queues(ctx.guild.id)

        async with ctx.typing():     
            is_link = re.match(URL_REGEX, url)

            if is_link and "list=" in url:
                await self.__add_playlist_to_queue(ctx, url, queue, force)

            else:
                await self.__add_song_to_queue(ctx, url, queue, is_link, force)
                
# виправити ймовірність не коректного посилання

    @commands.command()
    async def play(self, ctx, *, url):
        await ctx.message.delete()

        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        
        if not voice_channel:
            return await ctx.send("You're not in a voice channel!")
        
        if not ctx.voice_client:
            await voice_channel.connect()

        await self.__add_to_queue(ctx, url)

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def fplay(self, ctx, *, url):
        await ctx.message.delete()

        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        
        if not voice_channel:
            return await ctx.send("You're not in a voice channel!")
        
        if not ctx.voice_client:
            await voice_channel.connect()

        await self.__add_to_queue(ctx, url, True);

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def __prepare_song_info(self, queue):
        if not isinstance(queue[0], self._SongInfo):
            try:
                queue[0] = self.__extract_song_info(queue[0])
            except Exception as e:
                print(f"Error processing song: {str(e)}")
                queue.popleft()
                return None
        return queue[0]

    async def __play_audio(self, ctx, url, ffmpeg_options):
        source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
        self.songs_start_time[ctx.guild.id] = time.time()

    def __format_duration(self, duration):
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def __create_now_playing_embed(self, title, link, duration, thumbnail):
        formatted_duration = self.__format_duration(duration)
        embed = discord.Embed(
            title=" |◔◡◉| **Now Playing** :loud_sound:",
            description=f"Title: **[{title}]({link})**\n Duration: **{formatted_duration}**",
            color=discord.Color.green()
        )
        embed.set_author(name="Тут може бути ваша реклама", icon_url="https://img3.gelbooru.com//samples/cf/20/sample_cf20516f54dfff954bc364ca7a7d3c38.jpg")
        embed.set_thumbnail(url=thumbnail)
        return embed

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        
        manually_stopped = self.__get_manually_stopped(guild_id)
        
        if manually_stopped:
            print("manually_stopped")
            self.manually_stopped_flags[guild_id] = False
            return

        looped_song_info = self.__get_looped_song(guild_id)

        if looped_song_info is not None:
            await self.__play_audio(ctx, looped_song_info.url, FFMPEG_OPTIONS)
            return

        queue, history_queue = self.get_queues(guild_id)

        if not queue:
            embed = discord.Embed(title=" σ(≧ε≦σ) ♡ **Queue is empty!**", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        if await self.__prepare_song_info(queue) is None:
            await self.play_next(ctx)
            return

        song_info = queue.popleft()
        history_queue.append(song_info)

        await self.__play_audio(ctx, song_info.url, FFMPEG_OPTIONS)
        
        embed = self.__create_now_playing_embed(
            song_info.title, 
            song_info.link, 
            song_info.duration, 
            song_info.thumbnail
        )
        view = SerenadikView(self.client, ctx)
        
        await ctx.send(embed=embed, view=view)

        if not queue and not history_queue and ctx.voice_client.is_playing():
            embed = discord.Embed(title=" ٩(̾●̮̮̃̾•̃̾)۶ ", description=f"/////////////////", color=discord.Color.red())
            await ctx.send(embed=embed)
            
    async def __add_prev_to_queue(self, ctx):
        queue, history_queue = self.get_queues(ctx.guild.id)

        if not history_queue or len(history_queue) < 2:
            embed = discord.Embed(title=" σ(≧ε≦σ) ♡ **There no past songs!**", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return False
        
        queue.extendleft([history_queue.pop(), history_queue.pop()])
        return True

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            print("SKIP")
            ctx.voice_client.stop()
            #await ctx.send("The song is skipped ⏭")

    @commands.command()
    async def previous(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            if not await self.__add_prev_to_queue(ctx):
                return
            print("PREV")
            ctx.voice_client.stop()

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            # await ctx.send("The song is paused ⏸️")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
            # await ctx.send("The song continues to play ⏯️")

    @commands.command()
    async def loop(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            guild_id = ctx.guild.id
            loop_disabled = self.__get_looped_song(guild_id) is None
            if loop_disabled:
                _, history_queue = self.get_queues(guild_id)
                self.looped_songs[guild_id] = history_queue[-1]
            else:
                self.looped_songs[guild_id] = None
                
            await ctx.send(f"Looping for the current song was { 'enabled' if loop_disabled else 'disabled' } 🔄")

    @commands.command()
    async def seek(self, ctx, seconds: int):
        guild_id = ctx.guild.id
        
        _, history_queue = self.get_queues(guild_id)
        
        if not history_queue:
            await ctx.send("σ(≧ε≦σ) ♡ **There is no song playing currently!**")
            return

        song_info = history_queue[-1]
        url = song_info.url
        target_time = min(max(0, seconds), int(song_info.duration))

        FFMPEG_SEEK_OPTIONS = {
            **FFMPEG_OPTIONS,
            'before_options': f"-ss {target_time} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        }

        self.manually_stopped_flags[guild_id] = True
        ctx.voice_client.stop()
        await self.__play_audio(ctx, url, FFMPEG_SEEK_OPTIONS)

        embed = discord.Embed(
            title="⏩ **Seeked to a new time**",
            description=f"Current position set to **{target_time} seconds**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def forward(self, ctx, seconds: int):
        current_position = self.__get_current_playback_time(ctx.guild.id)
        target_time = current_position + seconds
        print(f"forward by {seconds} seconds")
        print(f"current_position: {current_position}")
        print(f"target_time: {target_time}")
        await self.seek(ctx, target_time)
        self.songs_start_time[ctx.guild.id] = time.time() - target_time
        
    @commands.command()
    async def backward(self, ctx, seconds: int):
        current_position = self.__get_current_playback_time(ctx.guild.id)
        target_time = current_position - seconds
        print(f"backward by {seconds} seconds")
        print(f"current_position: {current_position}")
        print(f"target_time: {target_time}")
        await self.seek(ctx, target_time)
        self.songs_start_time[ctx.guild.id] = time.time() - target_time

    def clear_queues(self, guild_id):
        queue, history_queue = self.get_queues(guild_id)
        queue.clear()
        history_queue.clear()

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            guild_id = ctx.guild.id
            self.clear_queues(guild_id)
            self.looped_songs[guild_id] = None
            self.manually_stopped_flags[guild_id] = True
            ctx.voice_client.stop()
            await ctx.send("Stopped the music and cleared the queue 🛑")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member):
        voice_client = discord.utils.get(self.client.voice_clients, guild=member.guild)
        
        if voice_client and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            self.clear_queues(member.guild.id)
            print(f"Everyone left the channel in guild {member.guild.id}, bot disconnected and queue cleared.")
    