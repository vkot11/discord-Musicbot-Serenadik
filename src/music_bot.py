import re
import time
import asyncio
import discord
from discord.ext import commands
from queue_manager import QueueManager
from control_view import SerenadikView
from embed_creator import EmbedCreator
from radio_handler import RadioHandler
from constants import FFMPEG_OPTIONS, URL_REGEX


class SerenadikBot(commands.Cog):

    _blacklisted_users = set()

    def __init__(self, client):
        self.client = client
        self.looped_songs = {}
        self.songs_start_time = {}
        self.manually_stopped_flags = {}
        self.queue_manager = QueueManager()
        self.radio_handler = RadioHandler()
        self.client.add_check(self.__globally_block)

    @staticmethod
    def ban_user(user_id: str):
        SerenadikBot._blacklisted_users.add(user_id)
    
    @staticmethod
    def unban_user(user_id: str):
        SerenadikBot._blacklisted_users.discard(user_id)
        
    async def __globally_block(self, ctx):
        if str(ctx.author.id) in SerenadikBot._blacklisted_users:
            await ctx.send("❀◕ ‿ ◕❀ The bot owner has banned you from using any commands")
            return False
        return True

    def get_looped_song(self, guild_id):
        if guild_id not in self.looped_songs:
            self.looped_songs[guild_id] = None
        return self.looped_songs[guild_id]

    def get_manually_stopped(self, guild_id):
        if guild_id not in self.manually_stopped_flags:
            self.manually_stopped_flags[guild_id] = False
        return self.manually_stopped_flags[guild_id]

    async def __add_to_queue(self, ctx, url, force=False):
        queue, _ = self.queue_manager.get_queues(ctx.guild.id)

        async with ctx.typing():     
            is_link = re.match(URL_REGEX, url)

            if is_link and "spotify" in url:
                await self.__handle_spotify_url(ctx, url, queue, force)

            elif is_link and "list=" in url:
                await self.queue_manager.add_playlist_to_queue(ctx, url, queue, force)

            else:
                await self.queue_manager.add_song_to_queue(ctx, url, queue, is_link, force)

    async def __handle_spotify_url(self, ctx, url, queue, force):
        if "track" in url:
            await self.queue_manager.add_spotify_song(ctx, url, queue, force)

        elif "playlist" in url:
            await self.queue_manager.add_spotify_playlist(ctx, url, queue, force)

        elif "album" in url:
            await self.queue_manager.add_spotify_album(ctx, url, queue, force)

    async def __play_audio(self, ctx, url, ffmpeg_options):
        source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
        self.songs_start_time[ctx.guild.id] = time.time()

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        manually_stopped = self.get_manually_stopped(guild_id)
        
        if manually_stopped:
            print("manually_stopped")
            self.manually_stopped_flags[guild_id] = False
            return

        looped_song_info = self.get_looped_song(guild_id)

        if looped_song_info is not None:
            await self.__play_audio(ctx, looped_song_info.url, FFMPEG_OPTIONS)
            return

        queue, history_queue = self.queue_manager.get_queues(guild_id)

        if not queue:
            await ctx.send(embed=EmbedCreator.create_empty_queue_embed())
            return

        if await self.queue_manager.prepare_song_info(queue) is None:
            await self.play_next(ctx)
            return

        song_info = queue.popleft()
        history_queue.append(song_info)

        await self.__play_audio(ctx, song_info.url, FFMPEG_OPTIONS)
        
        embed = EmbedCreator.create_now_playing_embed(
            song_info.title, 
            song_info.link, 
            song_info.duration, 
            song_info.thumbnail
        )
        view = SerenadikView(self.client, ctx)
        
        await ctx.send(embed=embed, view=view)

        if not queue and not history_queue and ctx.voice_client.is_playing():
            await ctx.send(embed=EmbedCreator.create_error_embed())

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

        await self.__add_to_queue(ctx, url, True)

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            print("SKIP")
            ctx.voice_client.stop()
            #await ctx.send("The song is skipped ⏭")

    @commands.command()
    async def previous(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            if not await self.queue_manager.add_prev_to_queue(ctx):
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
            loop_disabled = self.get_looped_song(guild_id) is None
            if loop_disabled:
                _, history_queue = self.queue_manager.get_queues(guild_id)
                self.looped_songs[guild_id] = history_queue[-1]
            else:
                self.looped_songs[guild_id] = None
                
            await ctx.send(f"Looping for the current song was { 'enabled' if loop_disabled else 'disabled' } 🔄")

    @commands.command()
    async def seek(self, ctx, seconds: int):
        guild_id = ctx.guild.id
        
        _, history_queue = self.queue_manager.get_queues(guild_id)
        
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
        
        await ctx.send(embed=EmbedCreator.create_seek_embed(target_time))

    def __get_current_playback_time(self, guild_id):
        if guild_id not in self.songs_start_time:
            return 0
        elapsed = max(0, time.time() - self.songs_start_time[guild_id])
        return int(elapsed)

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

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            guild_id = ctx.guild.id
            self.queue_manager.clear_queues(guild_id)
            self.looped_songs[guild_id] = None
            self.manually_stopped_flags[guild_id] = True
            ctx.voice_client.stop()
            await ctx.send("Stopped the music and cleared the queue 🛑")

    async def __play_radio(self, ctx, url):
        await ctx.message.delete()

        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        
        if not voice_channel:
            await ctx.send("You're not in a voice channel!")
            return False
        
        if not ctx.voice_client:
            await voice_channel.connect()

        if not ctx.voice_client.is_playing():
            await self.__play_audio(ctx, url, FFMPEG_OPTIONS)
            return True
            
        return False

    @commands.command()
    async def radio(self, ctx, *, url):
        if await self.__play_radio(ctx, url):
            embed_title = " |◔◡◉| **Radio Station** :loud_sound:"
            song_title = self.radio_handler.get_current_radio_song(url)
            embed = EmbedCreator.create_radio_embed(embed_title, song_title, discord.Color.orange())
            
            message = await ctx.send(embed=embed)
            
            asyncio.create_task(self.radio_handler.update_radio_message(ctx, embed, message, url))
            
    @commands.command()
    async def osu(self, ctx):
        osu_radio_url = 'https://radio.yas-online.net/listen/osustation'
        if await self.__play_radio(ctx, osu_radio_url):
            embed_title = " q(❂‿❂)p **Osu Radio Station** :loud_sound:"
            song_title = self.radio_handler.get_current_radio_song(osu_radio_url)
            embed = EmbedCreator.create_radio_embed(embed_title, song_title, discord.Color.pink())
            embed.set_author(name="osu!", icon_url="https://scontent-dus1-1.xx.fbcdn.net/v/t39.30808-6/296301322_155908430430719_4976778868501739810_n.png?_nc_cat=110&ccb=1-7&_nc_sid=6ee11a&_nc_ohc=GJy0hFvjXI4Q7kNvgH4_XhI&_nc_zt=23&_nc_ht=scontent-dus1-1.xx&_nc_gid=AHro3iBKVU5ndcLssrTBPj5&oh=00_AYCa51c-JkiZ4JXHWuVD7IrRzBypapelVlB4UJhL60HZjg&oe=673DCEB2")
            
            message = await ctx.send(embed=embed)
            
            asyncio.create_task(self.radio_handler.update_radio_message(ctx, embed, message, osu_radio_url))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member):
        voice_client = discord.utils.get(self.client.voice_clients, guild=member.guild)
        
        if voice_client and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            self.queue_manager.clear_queues(member.guild.id)
            print(f"Everyone left the channel in guild {member.guild.id}, bot disconnected and queue cleared.")
    
    @commands.command()
    async def info(self, ctx):
        await ctx.send(embed=EmbedCreator.create_info_embed())

    @commands.command()
    async def help(self, ctx):
        await ctx.send(embed=EmbedCreator.create_help_embed())
    