from discord import Embed
from discord import Color


class EmbedCreator:
    
    @staticmethod
    def format_duration(duration):
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    @staticmethod
    def create_now_playing_embed(title, link, duration, thumbnail):
        formatted_duration = EmbedCreator.format_duration(duration)
        embed = Embed(
            title=" |◔◡◉| **Now Playing** :loud_sound:",
            description=f"Title: **[{title}]({link})**\n Duration: **{formatted_duration}**",
            color=Color.green()
        )
        embed.set_author(
            name="Тут може бути ваша реклама", 
            icon_url="https://img3.gelbooru.com//samples/cf/20/sample_cf20516f54dfff954bc364ca7a7d3c38.jpg"
        )
        embed.set_thumbnail(url=thumbnail)
        return embed

    @staticmethod
    def create_radio_embed(title, song_title, color):
        return Embed(
            title=title,
            description=f"Now Playing: **{song_title}**",
            color=color
        )
    
    @staticmethod
    def create_playlist_added_embed(playlist_title, url, total_songs, force):
        return Embed(
            title=f" (♡μ_μ) **PLaylist added {'to the top' if force else 'to the end'}** :inbox_tray:",
            description=f"Title: **[{ playlist_title }]({ url })**\n Song count: **{ total_songs }**",
            color=Color.blue()
        )

    @staticmethod
    def create_song_added_embed(title, link, force):
        return Embed(
            title=f" (♡μ_μ) **Song added { 'to the top' if force else 'to the end' }** :inbox_tray:",
            description=f"Title: **[{ title }]({ link })**",
            color=Color.blue()
        )
    
    @staticmethod
    def create_empty_queue_embed():
        return Embed(title=" σ(≧ε≦σ) ♡ **Queue is empty!**", color=Color.orange())

    @staticmethod
    def create_no_past_songs_embed():
        return Embed(title=" σ(≧ε≦σ) ♡ **There no past songs!**", color=Color.orange())
    
    @staticmethod
    def create_seek_embed(target_time):
        return Embed(
            title="⏩ **Seeked to a new time**",
            description=f"Current position set to **{ target_time } seconds**.",
            color=Color.green()
        )

    @staticmethod
    def create_info_embed():
        return Embed(
            title="Info",
            description="Serenadik is a music bot designed to play songs from YouTube, Spotify, it is possible to turn on Osu radio and Normal radio",
            color=Color.dark_theme()
        )

    @staticmethod
    def create_help_embed():
        embed = Embed(
            title="Help Menu",
            description="List of available commands:",
            color=Color.greyple()
        )
        embed.add_field(
            name="**Main commands**:",
            value=(
                "`!help` — Show a list of available commands.\n"
                "`!play <url or text>` — Add a song to the queue and start playing.\n"
                "`!fplay <url or text>` — Add a song to the beginning of the queue and start playing.\n"
                "`!skip` — Skip the current song.\n"
                "`!previous` — Play previous song.\n"
                "`!pause` — Pause the current song.\n"
                "`!resume` — Continue playing the song.\n"
                "`!loop` — Enable or disable the repeat of the current song.\n"
                "`!stop` — Stop playback and clear the queue.\n"
                "`!seek <seconds>` — Rewind the song to the specified time.\n"
                "`!forward <seconds>` — Fast forward the specified number of seconds.\n"
                "`!backward <seconds>` — Rewind by the specified number of seconds.\n"
                "`!info` — Show information about the bot.\n"
            ),inline=False
        )
        
        embed.add_field(
            name="**Radio commands**:",
            value=(
                "`!osu` — Play Osu! Radio.\n"
                "`!radio <radio url>` — Play the radio station using the link.\n"
            ),
            inline=False
        )
        
        return embed
    
    @staticmethod
    def create_error_embed():
        return Embed(title=" ٩(̾●̮̮̃̾•̃̾)۶ ", description=f"/////////////////", color=Color.red())