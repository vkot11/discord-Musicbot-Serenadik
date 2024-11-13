import discord
from discord.ext import commands
import yt_dlp
import re
from ControlView import SerenadikView
import collections
from dataclasses import dataclass


FFMPEG_OPTIONS = {'options': '-vn', 
                  'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}
YDL_OPTIONS = {'format': 'bestaudio'}
YDL_OPTIONS_EXT = {
    'extract_flat': 'in_playlist',  
    'skip_download': True,          
    'quiet': True                   
}
URL_REGEX = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')

class SerenadikBot(commands.Cog):

    @dataclass
    class _VideoInfo:
        url: str
        title: str
        duration: str
        thumbnail: str
        link: str

    def __init__(self, client):
        self.client = client
        self.looped_songs = {}
        self.queues = {}
        self.history_queues = {}
        self.blacklisted_users = [279971956059537408]
        self.client.add_check(self.globally_block)
        self.ydl = yt_dlp.YoutubeDL(YDL_OPTIONS)
        self.ydl_ext = yt_dlp.YoutubeDL(YDL_OPTIONS_EXT)

    async def globally_block(self, ctx):
        if ctx.author.id in self.blacklisted_users:
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

    def __extract_video_info(self, url, search=False):
        if search:
            url = f"ytsearch:{url}"
        
        info = self.ydl.extract_info(url, download=False)

        if search and 'entries' in info:
            info = info['entries'][0]

        return self._VideoInfo(
            info['url'], 
            info['title'], 
            info['duration'], 
            info['thumbnail'], 
            info['webpage_url']
        )

    async def __add_playlist_to_queue(self, ctx, url, queue, force=False):
        try:
            playlist_info = self.ydl_ext.extract_info(url, download=False)
            total_videos = len(playlist_info['entries'])
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
                description=f"Title: **[{playlist_title}]({url})**\n Song count: **{total_videos}**",
                color=discord.Color.blue()
            )
            
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error processing playlist: {e}")

    async def __add_video_to_queue(self, ctx, url, queue, is_link=True, force=False):
        video_info = self.__extract_video_info(url, not is_link)
        queue.appendleft(video_info) if force else queue.append(video_info)

        embed = discord.Embed(
            title=f" (♡μ_μ) **Song added { "to the top" if force else "to the end" }** :inbox_tray:",
            description=f"Title: **[{video_info.title}]({video_info.link})**",
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
                await self.__add_video_to_queue(ctx, url, queue, is_link, force)
                
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

    async def __prepare_video_info(self, queue):
        if not isinstance(queue[0], self._VideoInfo):
            try:
                queue[0] = self.__extract_video_info(queue[0])
            except Exception as e:
                print(f"Error processing video: {str(e)}")
                queue.popleft()
                return None
        return queue[0]

    async def __play_audio(self, ctx, url):
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))

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
        looped_song_info = self.__get_looped_song(guild_id)
        
        if looped_song_info is not None:
            await self.__play_audio(ctx, looped_song_info.url)
            return

        queue, history_queue = self.get_queues(guild_id)

        if not queue:
            embed = discord.Embed(title=" σ(≧ε≦σ) ♡ **Queue is empty!**", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        if await self.__prepare_video_info(queue) is None:
            await self.play_next(ctx)
            return

        video_info = queue.popleft()
        history_queue.append(video_info)

        await self.__play_audio(ctx, video_info.url)
            
        embed = self.__create_now_playing_embed(
            video_info.title, 
            video_info.link, 
            video_info.duration, 
            video_info.thumbnail
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

    def clear_queues(self, guild):
        queue, history_queue = self.get_queues(guild.id)
        queue.clear()
        history_queue.clear()

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            self.clear_queues(ctx.guild)
            await ctx.send("Stopped the music and cleared the queue 🛑")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member):
        voice_client = discord.utils.get(self.client.voice_clients, guild=member.guild)
        
        if voice_client and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            self.clear_queues(member.guild)
            print(f"Everyone left the channel in guild {member.guild.id}, bot disconnected and queue cleared.")
