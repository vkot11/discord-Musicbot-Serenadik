import os
import spotipy
from dotenv import load_dotenv
from song_info import SongInfo
from playlist_info import PlaylistInfo
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


class SpotifyClient:
    def __init__(self):
        self.client = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                cache_handler=None  
            )
        )

    def get_track_info(self, url):
        return self.__get_track_info(url)

    def get_playlist_info(self, url):
        return self.__get_playlist_info(url)

    def get_album_info(self, url):
        return self.__get_album_info(url)

    def __get_track_info(self, url):
        track_id = url.split('/')[-1].split('?')[0]
        track = self.client.track(track_id)
        return SongInfo(
            url=track['external_urls']['spotify'],
            title=track['name'],
            artist=track['artists'][0]['name'],
            thumbnail=track['album']['images'][0]['url'],
            duration=track['duration_ms'] // 1000
        )

    def __get_playlist_info(self, url):
        playlist_id = url.split('/')[-1].split('?')[0]
        playlist = self.client.playlist(playlist_id)
        tracks = playlist['tracks']['items']
        return PlaylistInfo(
            title=playlist['name'],
            total_songs=len(tracks),
            songs=[
                SongInfo(
                    title=track['track']['name'],
                    artist=track['track']['artists'][0]['name'],
                    url=track['track']['external_urls']['spotify'],
                    thumbnail=track['track']['album']['images'][0]['url'],
                    duration=track['track']['duration_ms'] // 1000
                )
                for track in tracks
            ]
        )

    def __get_album_info(self, url):
        album_id = url.split('/')[-1].split('?')[0]
        album = self.client.album(album_id)
        tracks = album['tracks']['items']
        return PlaylistInfo(
            title=album['name'],
            total_songs=len(tracks),
            songs=[
                SongInfo(
                    title=track['name'],
                    artist=track['artists'][0]['name'],
                    url=track['external_urls']['spotify'],
                    thumbnail=album['images'][0]['url'],
                    duration=track['duration_ms'] // 1000
                )
                for track in tracks
            ]
        )