from functools import lru_cache
import yt_dlp
from song_info import SongInfo
from playlist_info import PlaylistInfo
import os

class YdlProcessor:
    cache_size = 100

    def __init__(self, cache_size=100):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_path = os.path.join(current_dir, "..", "cook_convert.txt")

        YDL_OPTIONS = {
            'format': 'bestaudio',
            'noplaylist': True,
            'nocheckcertificate': True,
            'no_color': True,
            'verbose': True,
#            'cookiefile': "/home/eagle/MS-testcd/discord-Musicbot-Serenadik/cook_convert.txt"
            'cookiefile': cookies_path
        }

        YDL_OPTIONS_EXT = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'quiet': True,
#            'cookiefile': "/home/eagle/MS-testcd/discord-Musicbot-Serenadik/cook_convert.txt"
            'cookiefile': cookies_path
        } 

        self.ydl = yt_dlp.YoutubeDL(YDL_OPTIONS)
        self.ydl_ext = yt_dlp.YoutubeDL(YDL_OPTIONS_EXT)
        YdlProcessor.cache_size = cache_size
        
    @lru_cache(maxsize=cache_size)
    def __cached_extract_info(self, url):
        return self.ydl.extract_info(url, download=False)

    def extract_song_info(self, url, search=False):
        if search:
            url = f"ytsearch:{url}"

        info = self.__cached_extract_info(url)

        if search and 'entries' in info:
            info = info['entries'][0]

        return SongInfo(
            url=info['url'],
            title=info['title'],
            duration=info['duration'],
            thumbnail=info['thumbnail'],
            link=info['webpage_url']
        )

    def extract_playlist_info(self, url):
        playlist_info = self.ydl_ext.extract_info(url, download=False)
        entries = playlist_info['entries']
        
        return PlaylistInfo(
            title=playlist_info.get('title', 'Mix Youtube'),
            total_songs=len(entries),
            songs=entries
        )

    