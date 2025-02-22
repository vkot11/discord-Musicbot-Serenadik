import re
import random
import collections
from song_info import SongInfo
from constants import URL_REGEX
from spotify import SpotifyClient
from embed_creator import EmbedCreator
from ydl_processor import YdlProcessor


class QueueManager:
    def __init__(self):
        self.queues = {}
        self.history_queues = {}
        self.ydl_processor = YdlProcessor()
        self.spotify_client = SpotifyClient() 
        
    def get_queues(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = collections.deque()
            self.history_queues[guild_id] = []
        return (self.queues[guild_id], self.history_queues[guild_id])
    
    def clear_queues(self, guild_id):
        queue, history_queue = self.get_queues(guild_id)
        queue.clear()
        history_queue.clear()
        
    def shuffle_queue(self, guild_id):
        queue, _ = self.get_queues(guild_id)
        if queue:
            random.shuffle(queue)

    async def prepare_song_info(self, queue):
        if not isinstance(queue[0], SongInfo):
            try:
                is_link = re.match(URL_REGEX, queue[0])
                queue[0] = self.ydl_processor.extract_song_info(queue[0], not is_link)
            except Exception as e:
                print(f"Error processing video__prepare_song_info: {str(e)}")
                queue.popleft()
                return None
        return queue[0]

    async def add_song_to_queue(self, ctx, url, queue, is_link=True, force=False, flag="default"):
        song_info = self.ydl_processor.extract_song_info(url, not is_link)
        song_info.flag = flag
        queue.appendleft(song_info) if force else queue.append(song_info)

        embed = EmbedCreator.create_song_added_embed(song_info.title, song_info.link, force)
        await ctx.send(embed=embed)

    def __configure_append_method(self, queue, entries, force=False):        
        if force:
            return queue.appendleft, reversed(entries)
            
        return queue.append, entries

    async def add_playlist_to_queue(self, ctx, url, queue, force=False):
        try:
            playlist_info = self.ydl_processor.extract_playlist_info(url)
            
            append_method, playlist_entries = self.__configure_append_method(queue, playlist_info.songs, force)

            for entry in playlist_entries:
                append_method(entry['url'])

            embed = EmbedCreator.create_mix_added_embed(playlist_info.title, url, playlist_info.total_songs, force, 'Playlist')
            
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error processing playlist-add_playlist_to_queue: {e}")
            
    async def add_spotify_song(self, ctx, url, queue, force):
        spotify_info = self.spotify_client.get_track_info(url)
        search_query = f"{ spotify_info.title } { spotify_info.artist }"

        await self.add_song_to_queue(ctx, search_query, queue, None, force)

    async def __add_multiple_spotify_tracks(self, ctx, url, queue, mix_info, force):
        append_method, playlist_tracks = self.__configure_append_method(queue, mix_info.songs, force)

        for track in playlist_tracks:
            youtube_url = f"{ track.title } { track.artist }"
            append_method(youtube_url)

    async def add_spotify_playlist(self, ctx, url, queue, force):
        playlist_info = self.spotify_client.get_playlist_info(url)
        await self.__add_multiple_spotify_tracks(ctx, url, queue, playlist_info, force)
        
        embed = EmbedCreator.create_mix_added_embed(playlist_info.title, url, playlist_info.total_songs, force, 'Playlist')
        await ctx.send(embed=embed)
        
    async def add_spotify_album(self, ctx, url, queue, force):
        album_info = self.spotify_client.get_album_info(url)
        await self.__add_multiple_spotify_tracks(ctx, url, queue, album_info, force)
        
        embed = EmbedCreator.create_mix_added_embed(album_info.title, url, album_info.total_songs, force, 'Album')
        await ctx.send(embed=embed)
        
    async def add_prev_to_queue(self, ctx, queue_ended):
        queue, history_queue = self.get_queues(ctx.guild.id)

        if queue_ended:
            queue.appendleft(history_queue.pop())
            return True

        if not history_queue or len(history_queue) < 2:
            embed = EmbedCreator.create_no_past_songs_embed()
            await ctx.send(embed=embed)
            return False

        queue.extendleft([history_queue.pop(), history_queue.pop()])
        return True
