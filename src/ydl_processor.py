from functools import lru_cache
import yt_dlp
from song_info import SongInfo
from playlist_info import PlaylistInfo

import time

class YdlProcessor:
    cache_size = 100

    def __init__(self, cache_size=100):
        YDL_OPTIONS = {
            'format': 'bestaudio',
            'noplaylist': True,
            'nocheckcertificate': True,
            'no_color': True,
            'age_limit': 0
        }

        YDL_OPTIONS_EXT = {
            'extract_flat': 'in_playlist',  
            'skip_download': True,          
            'quiet': True                   
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

        t1 = time.time()

        info = self.__cached_extract_info(url)

        if search and 'entries' in info:
            info = info['entries'][0]

        t2 = time.time()
        print(f"exec time: { t2-t1 }")

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

    