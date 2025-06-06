from functools import lru_cache
import yt_dlp
from song_info import SongInfo
from playlist_info import PlaylistInfo
import os

class YdlProcessor:
    cache_size = 100
    def __init__(self, cache_size=100):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_path = os.path.join(current_dir, "..", "cookies/cookies_file.txt")

        YDL_OPTIONS = {
            'format': 'bestaudio',
            'noplaylist': True,
            'nocheckcertificate': True,
            'no_color': True,
            # 'verbose': True,
            'cookiefile': cookies_path,
        }

        YDL_OPTIONS_EXT = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'quiet': True,
            'cookiefile': cookies_path,

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
            info = info.get('entries')[0]

        return SongInfo(
            url=info.get('url'),
            title=info.get('title'),
            duration=info.get('duration'),
            thumbnail=info.get('thumbnail'),
            link=info.get('webpage_url')
        )

    def extract_playlist_info(self, url):
        playlist_info = self.ydl_ext.extract_info(url, download=False)
        entries = playlist_info.get('entries')
        
        return PlaylistInfo(
            title=playlist_info.get('title', 'Mix Youtube'),
            total_songs=len(entries),
            songs=entries
        )

    