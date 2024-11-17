import yt_dlp
from song_info import SongInfo
from playlist_info import PlaylistInfo
from constants import YDL_OPTIONS, YDL_OPTIONS_EXT

class YdlProcessor:
    def __init__(self):
        self.youtube_search_cache = {}
        self.ydl = yt_dlp.YoutubeDL(YDL_OPTIONS)
        self.ydl_ext = yt_dlp.YoutubeDL(YDL_OPTIONS_EXT)
        
    def extract_song_info(self, url, search=False):
        if search:
            if url in self.youtube_search_cache:
                return self.youtube_search_cache[url]
            url = f"ytsearch:{url}"
        
        info = self.ydl.extract_info(url, download=False)
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

    