import os
import re
import time
import asyncio
import discord
import datetime
import yt_dlp
import color_palette as cpl
from discord.ext import commands
from queue_manager import QueueManager
from control_view import SerenadikView
from embed_creator import EmbedCreator
from radio_handler import RadioHandler
from constants import FFMPEG_OPTIONS, FFMPEG_NIGHTCORE_OPTIONS, FFMPEG_BASSBOOST_OPTIONS, FFMPEG_SLOW_REVERB_OPTIONS, URL_REGEX


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
        self.ffmpeg_flag_options  = {
            'default': FFMPEG_OPTIONS, 
            'ncore': FFMPEG_NIGHTCORE_OPTIONS, 
            'bboost': FFMPEG_BASSBOOST_OPTIONS,
            'slowrb': FFMPEG_SLOW_REVERB_OPTIONS,
        }

    @staticmethod
    def ban_user(user_id: str):
        SerenadikBot._blacklisted_users.add(user_id)
    
    @staticmethod
    def unban_user(user_id: str):
        SerenadikBot._blacklisted_users.discard(user_id)
        
    async def __globally_block(self, ctx):
        if str(ctx.author.id) in SerenadikBot._blacklisted_users:
            await ctx.send("**❀◕ ‿ ◕❀ The bot owner has banned you from using any commands**")
            return False
        return True

    def user_interaction_info(self, ctx, user, color: str, command: str):
        if not user:
            user = ctx.author

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{cpl.BG_COLORS['Bright Black']}{timestamp}{cpl.RESET}{cpl.COLORS['Cyan']} | {user.display_name} | {user.name} | {user.id} |{cpl.COLORS[color]} command: {command}{cpl.RESET}") 
    
    def get_looped_song(self, guild_id):
        if guild_id not in self.looped_songs:
            self.looped_songs[guild_id] = None
        return self.looped_songs[guild_id]

    def get_manually_stopped(self, guild_id):
        if guild_id not in self.manually_stopped_flags:
            self.manually_stopped_flags[guild_id] = False
        return self.manually_stopped_flags[guild_id]

    def get_ffmpeg_options(self, flag='default'):
        return self.ffmpeg_flag_options.get(flag.lower(), 'default')

    def __flags_contains(self, flag: str):
        return flag in self.ffmpeg_flag_options

    def __parse_flag_from_query(self, query: str) -> tuple[str, str]:
        words = query.split()
        last_word = words[-1].lower()
        
        if (self.__flags_contains(last_word)):
            return ' '.join(words[:-1]), last_word
        
        return query, 'default'

    async def __add_to_queue(self, ctx, url, force=False, flag="default"):
        queue, _ = self.queue_manager.get_queues(ctx.guild.id)

        async with ctx.typing():     
            is_link = re.match(URL_REGEX, url)

            if is_link and "spotify" in url:
                await self.__handle_spotify_url(ctx, url, queue, force)

            elif is_link and "list=" in url:
                await self.queue_manager.add_playlist_to_queue(ctx, url, queue, force)

            else:
                await self.queue_manager.add_song_to_queue(ctx, url, queue, is_link, force, flag)

    async def __handle_spotify_url(self, ctx, url, queue, force):
        if "track" in url:
            await self.queue_manager.add_spotify_song(ctx, url, queue, force)

        elif "playlist" in url:
            await self.queue_manager.add_spotify_playlist(ctx, url, queue, force)

        elif "album" in url:
            await self.queue_manager.add_spotify_album(ctx, url, queue, force)

    async def __play_audio(self, ctx, url, ffmpeg_options):
        ffmpeg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bin/ffmpeg.exe"))
        source = await discord.FFmpegOpusAudio.from_probe(
            url,
            executable=ffmpeg_path,
            **ffmpeg_options
        )

        ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
        self.songs_start_time[ctx.guild.id] = time.time()

    async def play_next(self, ctx, user=None):
        guild_id = ctx.guild.id
        manually_stopped = self.get_manually_stopped(guild_id)
        
        if manually_stopped:
            self.user_interaction_info(ctx, user, "Red", "STOP")
            self.manually_stopped_flags[guild_id] = False
            return

        looped_song_info = self.get_looped_song(guild_id)
        
        if looped_song_info is not None:
            await self.__play_audio(ctx, looped_song_info.url, self.get_ffmpeg_options(looped_song_info.flag))
            return

        queue, history_queue = self.queue_manager.get_queues(guild_id)

        if not queue:
            await ctx.send(embed=EmbedCreator.create_empty_queue_embed())
            return

        if ctx.voice_client:
            if await self.queue_manager.prepare_song_info(queue) is None:
                await self.play_next(ctx)
        else:
            self.queue_manager.clear_queues(guild_id)
            self.looped_songs[guild_id] = None
            self.manually_stopped_flags[guild_id] = False
            return
        
        
        song_info = queue.popleft()
        history_queue.append(song_info)

        await self.__play_audio(ctx, song_info.url, self.get_ffmpeg_options(song_info.flag))
        
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

    def get_youtube_stream_url(self, url):
        ydl_opts = {
            'format': 'bestaudio', 
            'noplaylist': True, 
            'quiet': True 
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')

    @commands.command()
    async def getsource(self, ctx, url):
        stream_url = self.get_youtube_stream_url(url)
        
        if not stream_url:
            await ctx.send("Не вдалося отримати аудіопотік зі стріму!")
            return

        await ctx.send(f"🔗 Пряме посилання на аудіо: `{stream_url}`")


    @commands.command()
    async def play(self, ctx, *, query):
        await ctx.message.delete()
        
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        
        if not voice_channel:
            return await ctx.send("You're not in a voice channel!")
        
        if not ctx.voice_client:
            await voice_channel.connect()
        
        url, flag = self.__parse_flag_from_query(query)

        await self.__add_to_queue(ctx, url, False, flag)
            
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def fplay(self, ctx, *, query):
        await ctx.message.delete()

        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        
        if not voice_channel:
            return await ctx.send("You're not in a voice channel!")
        
        if not ctx.voice_client:
            await voice_channel.connect()

        url, flag = self.__parse_flag_from_query(query)

        await self.__add_to_queue(ctx, url, True, flag)
        
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx, user=None):
        if ctx.voice_client and ctx.voice_client.is_playing():
            self.user_interaction_info(ctx, user, "Bright Red", "SKIP")
            ctx.voice_client.stop()

    @commands.command()
    async def previous(self, ctx, user=None):
        if not ctx.voice_client:   
            return
        
        queue_playing = ctx.voice_client.is_playing()

        if not await self.queue_manager.add_prev_to_queue(ctx, not queue_playing):
            return
        
        self.user_interaction_info(ctx, user, "Bright Magenta", "PREV")
        
        if queue_playing:
            ctx.voice_client.stop()
                
        else:
            await self.play_next(ctx)

    @commands.command()
    async def pause(self, ctx, user):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            self.user_interaction_info(ctx, user, "Green", "PAUSE")

    @commands.command()
    async def resume(self, ctx, user):
        if ctx.voice_client and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
            self.user_interaction_info(ctx, user, "Green", "RESUME")

    @commands.command()
    async def loop(self, ctx, user):
        if ctx.voice_client and ctx.voice_client.is_playing():
            guild_id = ctx.guild.id
            loop_disabled = self.get_looped_song(guild_id) is None
            if loop_disabled:
                _, history_queue = self.queue_manager.get_queues(guild_id)
                self.looped_songs[guild_id] = history_queue[-1]
            else:
                self.looped_songs[guild_id] = None
            
            self.user_interaction_info(ctx, user, "Bright Green", "LOOP")

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
            **self.get_ffmpeg_options(song_info.flag),
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

        print(f"{cpl.COLORS['Yellow']}forward by {seconds} seconds")
        print(f"current_position: {current_position}")
        print(f"target_time: {target_time}{cpl.RESET}")

        await self.seek(ctx, target_time)
        self.songs_start_time[ctx.guild.id] = time.time() - target_time
        
    @commands.command()
    async def backward(self, ctx, seconds: int):
        current_position = self.__get_current_playback_time(ctx.guild.id)
        target_time = current_position - seconds

        print(f"{cpl.COLORS['Yellow']}forward by {seconds} seconds")
        print(f"current_position: {current_position}")
        print(f"target_time: {target_time}{cpl.RESET}")
        
        await self.seek(ctx, target_time)
        self.songs_start_time[ctx.guild.id] = time.time() - target_time

    @commands.command()
    async def shuffle(self, ctx, user):
        self.queue_manager.shuffle_queue(ctx.guild.id)
        self.user_interaction_info(ctx, user, "Bright Cyan", "SHUFFLE")

        await ctx.send("The queue was shuffled! ♪(┌・。・)┌")

    @commands.command()
    async def stop(self, ctx, user):
        if ctx.voice_client:
            guild_id = ctx.guild.id
            
            ctx.voice_client.stop()

            self.queue_manager.clear_queues(guild_id)
            self.looped_songs[guild_id] = None
            self.manually_stopped_flags[guild_id] = True
            
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


    # @commands.command()
    # async def playfile(self, ctx, filename: str = "audio.mp3"):
    #     """Відтворює mp3 файл з директорії проекту"""
    #     await ctx.message.delete()
        
    #     # Перевірка, чи користувач у голосовому каналі
    #     voice_channel = ctx.author.voice.channel if ctx.author.voice else None
    #     if not voice_channel:
    #         await ctx.send("You're not in a voice channel!")
    #         return
        
    #     # Підключення до голосового каналу, якщо бот ще не підключений
    #     if not ctx.voice_client:
    #         await voice_channel.connect()
        
    #     try:
    #         # Формування абсолютного шляху до файлу
    #         file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
            
    #         # Перевірка існування файлу
    #         if not os.path.exists(file_path):
    #             await ctx.send(f"File '{filename}' not found!")
    #             return
            
    #         # Перевірка формату файлу
    #         if not filename.lower().endswith('.mp3'):
    #             await ctx.send("Only .mp3 files are supported!")
    #             return
            
    #         # Шлях до ffmpeg.exe
    #         ffmpeg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bin/ffmpeg.exe"))
            
    #         if not os.path.exists(ffmpeg_path):
    #             await ctx.send("FFmpeg not found! Please ensure it's installed correctly.")
    #             return
            
    #         # Створення аудіоджерела
    #         source = discord.PCMVolumeTransformer(
    #             discord.FFmpegPCMAudio(
    #                 file_path,
    #                 executable=ffmpeg_path,
    #                 options='-vn'
    #             )
    #         )
            
    #         # Функція для обробки завершення відтворення
    #         def after_playing(error):
    #             try:
    #                 if error:
    #                     print(f"Playback finished with error: {error}")
    #                 else:
    #                     print(f"Successfully finished playing {filename}")
    #             except Exception as e:
    #                 print(f"Error in after_playing: {e}")
            
    #         # Відтворення файлу
    #         if ctx.voice_client.is_playing():
    #             ctx.voice_client.stop()
            
    #         ctx.voice_client.play(source, after=after_playing)
            
    #         # Логування
    #         self.user_interaction_info(ctx, None, "Bright Cyan", f"PLAYFILE {filename}")
            
    #         # Повідомлення про відтворення
    #         embed = EmbedCreator.create_now_playing_embed(
    #             title=f"Playing local file: {filename}",
    #             link=None,
    #             duration=None,
    #             thumbnail=None
    #         )
    #         await ctx.send(embed=embed)
            
    #     except discord.errors.ClientException as ce:
    #         await ctx.send(f"Client error: {str(ce)}")
    #         print(f"ClientException: {str(ce)}")
    #     except Exception as e:
    #         await ctx.send(f"Error playing file: {str(e)}")
    #         print(f"Error playing file: {str(e)}")

    @commands.command()
    async def osu(self, ctx):
        osu_radio_url = 'https://radio.yas-online.net/listen/osustation'
        if await self.__play_radio(ctx, osu_radio_url):
            embed_title = " q(❂‿❂)p **Osu Radio Station** :loud_sound:"
            song_title = self.radio_handler.get_current_radio_song(osu_radio_url)
            embed = EmbedCreator.create_radio_embed(embed_title, song_title, discord.Color.pink())
            embed.set_author(name="osu!", icon_url="https://upload.wikimedia.org/wikipedia/en/2/29/Osu%21_logo_2024%2C_no_dot.png?20240518000302")
            
            message = await ctx.send(embed=embed)
            
            asyncio.create_task(self.radio_handler.update_radio_message(ctx, embed, message, osu_radio_url))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member):
        voice_client = discord.utils.get(self.client.voice_clients, guild=member.guild)
        if voice_client and voice_client.channel:
            await asyncio.sleep(60)

            if len(voice_client.channel.members) == 1:
                await voice_client.disconnect()
                self.queue_manager.clear_queues(member.guild.id)
                print(f"{cpl.COLORS['Yellow']}Bot left the channel in guild {member.guild.id} after 60 sec of being alone {cpl.RESET}")
    
    @commands.Cog.listener()
    async def on_voice_channel_update(self, member, before, after):
        if member == self.client.user:
            if before.channel != after.channel:
                if after.channel:
                    voice_client = discord.utils.get(self.client.voice_clients, guild=member.guild)
                    if voice_client and voice_client.is_playing():
                        voice_client.pause()
                        await asyncio.sleep(0.5)
                        voice_client.resume()

    # temporary command to fix bugs 
    @commands.command()
    async def playlist_info(self, ctx):
        queue, _ = self.queue_manager.get_queues(ctx.guild.id)
        queue_length = len(queue)

        await ctx.send(f"🎶 Currently, there are **{queue_length}** songs in the playlist!")


    @commands.command()
    async def info(self, ctx):
        await ctx.send(embed=EmbedCreator.create_info_embed())

    @commands.command()
    async def help(self, ctx):
        await ctx.send(embed=EmbedCreator.create_help_embed())
    