import discord
from discord.ext import commands
import yt_dlp
import re
from ControlView import SerenadikView
import collections

FFMPEG_OPTIONS = {'options': '-vn', 
                  'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}
YDL_OPTIONS = {'format': 'bestaudio'}
YDL_OPTIONS_ext = {
    'extract_flat': 'in_playlist',  
    'skip_download': True,          
    'quiet': True                   
}
URL_REGEX = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')

class SerenadikBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queues = {}
        self.blacklisted_users = [279971956059537408]

        self.client.add_check(self.globally_block)


    async def globally_block(self, ctx):
        if ctx.author.id in self.blacklisted_users:
            await ctx.send("❀◕ ‿ ◕❀ The bot owner has banned you from using any commands")
            return False
        return True
    
    
    def get_dequeue(self, guild):
        if guild.id not in self.queues:
            self.queues[guild.id] = collections.deque()
        return self.queues[guild.id]

# виправити ймовірність не коректного посилання

    @commands.command()
    async def play(self, ctx, *, url):
        await ctx.message.delete()

        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        
        if not voice_channel:
            return await ctx.send("You're not in a voice channel!")
        
        if not ctx.voice_client:
            await voice_channel.connect()

        queue = self.get_dequeue(ctx.guild)

        async with ctx.typing():
            if re.match(URL_REGEX, url):
                if "list=" in url:
                    try:
                        with yt_dlp.YoutubeDL(YDL_OPTIONS_ext) as ydl:
                            playlist_info = ydl.extract_info(url, download=False)
                            total_videos = len(playlist_info['entries'])
                            playlist_title = playlist_info.get('title', 'Mix Youtube') 
                            count_of_songs = 1
                            
                            for entry in playlist_info['entries']:
                                print(f"-------------------ADDED {count_of_songs} SONG TO LIST--------")
                                queue.append((entry['url'], 0))
                                count_of_songs += 1
                        
                        embed = discord.Embed(
                            title=" (♡μ_μ) **PLaylist added** :inbox_tray:",
                            description=f"Title: **[{playlist_title}]({url})**\n Song count: **{total_videos}**",
                            color=discord.Color.blue()
                        )

                        await ctx.send(embed=embed)

                    except Exception as e:
                        await ctx.send(f"Error processing playlist: {e}")
                            
                else:
                    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(url, download=False)
                        title = info['title']
                        url_new = info['url']
                        duration = info['duration']
                        thumbnail = info['thumbnail']
                        link = info['webpage_url']
                        queue.append((url_new, title, duration, thumbnail, link))

                    embed = discord.Embed(
                            title=" (♡μ_μ) **Link added** :inbox_tray:",
                            description=f"Title: **[{title}]({url})**",
                            color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
            else:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(f"ytsearch:{url}", download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    url_new = info['url']
                    title = info['title']
                    duration = info['duration']
                    thumbnail = info['thumbnail']
                    link = info['webpage_url']
                    queue.append((url_new, title, duration, thumbnail, link))

                embed = discord.Embed(
                    title=" (♡μ_μ) **Song added** :inbox_tray:",
                    description=f"Title: **{title}**",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)

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

        queue = self.get_dequeue(ctx.guild)

        async with ctx.typing():
            if re.match(URL_REGEX, url):
                if "list=" in url:
                    try:
                        with yt_dlp.YoutubeDL(YDL_OPTIONS_ext) as ydl:
                            playlist_info = ydl.extract_info(url, download=False)
                            total_videos = len(playlist_info['entries'])
                            playlist_title = playlist_info.get('title', 'Mix Youtube') 
                            count_of_songs = 1

                            for entry in reversed(playlist_info['entries']):
                                print(f"-------------------ADDED {count_of_songs} SONG TO LIST--------")
                                queue.appendleft((entry['url'], 0))
                                count_of_songs += 1
                        
                        print(queue)
                        embed = discord.Embed(
                            title=" (♡μ_μ) **PLaylist added** :inbox_tray:",
                            description=f"Title: **[{playlist_title}]({url})**\n Song count: **{total_videos}**",
                            color=discord.Color.blue()
                        )

                        await ctx.send(embed=embed)

                    except Exception as e:
                        await ctx.send(f"Error processing playlist: {e}")
                            
                else:
                    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(url, download=False)
                        title = info['title']
                        url_new = info['url']
                        duration = info['duration']
                        thumbnail = info['thumbnail']
                        link = info['webpage_url']
                        queue.appendleft((url_new, title, duration, thumbnail, link))

                    embed = discord.Embed(
                            title=" (♡μ_μ) **Link added** :inbox_tray:",
                            description=f"Title: **[{title}]({url})**",
                            color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
            else:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(f"ytsearch:{url}", download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    url_new = info['url']
                    title = info['title']
                    duration = info['duration']
                    thumbnail = info['thumbnail']
                    link = info['webpage_url']
                    queue.appendleft((url_new, title, duration, thumbnail, link))

                embed = discord.Embed(
                    title=" (♡μ_μ) **Song added** :inbox_tray:",
                    description=f"Title: **{title}**",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        print("TRUE")
        queue = self.get_dequeue(ctx.guild)

        if not queue:
            embed = discord.Embed(title=" σ(≧ε≦σ) ♡ **Queue is empty!**", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        try:
            if queue[0][1] == 0:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(queue[0][0], download=False)
                    title = info['title']
                    url = info['url']
                    duration = info['duration']
                    thumbnail = info['thumbnail']
                    link = info['webpage_url']
                    queue[0] = (url, title, duration, thumbnail, link)

        except Exception as e:
            error_message = str(e)
            print(f"Error processing video: {error_message}")
            queue.popleft()
            await self.play_next(ctx)

            return

        if queue:
            url, title, duration, thumbnail, link = queue.popleft()

            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_duration = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))

# ////////////////////-embed menu jopta-//////////////////
            embed = discord.Embed(
                title=" |◔◡◉| **Now Playing** :loud_sound:",
                description=f"Title: **[{title}]({link})**\n Duration: **{formatted_duration}**",
                color=discord.Color.green()
            )
            embed.set_author(name="Тут може бути ваша реклама", icon_url="https://img3.gelbooru.com//samples/cf/20/sample_cf20516f54dfff954bc364ca7a7d3c38.jpg")
            embed.set_thumbnail(url=thumbnail)
# ////////////////////-end of embed menu typa-//////////////////

            view = SerenadikView(self.client, ctx)
            await ctx.send(embed=embed, view=view)

        elif not ctx.voice_client.is_playing():
            embed = discord.Embed(title=" ٩(̾●̮̮̃̾•̃̾)۶ ", description=f"/////////////////", color=discord.Color.red())
            await ctx.send(embed=embed)
            
    # @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            # await ctx.send("The song is skipped ⏭")

    # @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("The song is paused ⏸️")

    # @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
            await ctx.send("The song continues to play ⏯️")


    # @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            self.get_dequeue(ctx.guild).clear()
    #         await ctx.send(Stopped the music and cleared the queue 🛑)
    

    @commands.Cog.listener()
    async def on_voice_state_update(self, member):
        voice_client = discord.utils.get(self.client.voice_clients, guild=member.guild)
        
        if voice_client and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            self.get_dequeue(member.guild).clear()
            print(f"Everyone left the channel in guild {member.guild.id}, bot disconnected and queue cleared.")
