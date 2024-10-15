import discord
from discord.ext import commands
import yt_dlp
import re
from pytube import Playlist
from ControlView import SerenadikView

FFMPEG_OPTIONS = {'options': '-vn', 
                  'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}
YDL_OPTIONS = {'format': 'bestaudio'}
URL_REGEX = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')

class SerenadikBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queues = {}
        self.blacklisted_users = [279971956059537408, 416222621068296203]

        self.client.add_check(self.globally_block)


    async def globally_block(self, ctx):
        if ctx.author.id in self.blacklisted_users:
            if 416222621068296203 in self.blacklisted_users:
                await ctx.send("❀◕ ‿ ◕❀ if you don't want to play Osu, you won't play musicbot")
            else:
                await ctx.send("❀◕ ‿ ◕❀ The bot owner has banned you from using any commands")
            return False
        return True
    
    
    def get_queue(self, guild):
        if guild.id not in self.queues:
            self.queues[guild.id] = []
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

        queue = self.get_queue(ctx.guild)

        async with ctx.typing():
            if re.match(URL_REGEX, url):
                if "list=" in url:
                    try:
                        playlist = Playlist(url)
                        for video_url in playlist.video_urls:
                            print("-------------------ADDED 1 SONG TO LIST--------")
                            queue.append((video_url, 0))
                        embed = discord.Embed(
                            title=" (♡μ_μ) **PLaylist added** :inbox_tray:",
                            description=f"Title: **[{playlist.title}]({playlist.playlist_url})**\n Count: **{playlist.length}**",
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

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild)

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
            print(f"Error processing playlist: {e}")

        if queue:
            url, title, duration, thumbnail, link = queue.pop(0)

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
            await ctx.send("The song is skipped ⏭")

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
            self.get_queue(ctx.guild).clear()
    #         await ctx.send(Stopped the music and cleared the queue 🛑)
    

    @commands.Cog.listener()
    async def on_voice_state_update(self, member):
        voice_client = discord.utils.get(self.client.voice_clients, guild=member.guild)
        
        if voice_client and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
            self.get_queue(member.guild).clear()
            print(f"Everyone left the channel in guild {member.guild.id}, bot disconnected and queue cleared.")
