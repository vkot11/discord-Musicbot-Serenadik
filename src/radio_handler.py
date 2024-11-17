import re
import asyncio
import requests

class RadioHandler:
    def get_current_radio_song(self, url):
        headers = {"Icy-MetaData": "1"}
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=5)
            if not response.headers.get("icy-metaint"):
                return ""
            
            metaint = int(response.headers["icy-metaint"])
            response.raw.read(metaint)
            metadata = response.raw.read(255).split(b"StreamTitle='")[1]
            stream_title = metadata.split(b"';")[0].decode("utf-8")
            
            title = re.sub(r"^\d+\s*", "", stream_title)
            title = title.replace(".mp3", "").strip()
            return title
            
        except Exception as e:
            print(f"Error: {e}")
            return ""

    async def update_radio_message(self, ctx, embed, message, url):
        while ctx.voice_client and ctx.voice_client.is_playing():
            try:
                await asyncio.sleep(10)
                if not ctx.voice_client:
                    break
                song_title = self.get_current_radio_song(url)
                embed.description = f"Now Playing: **{song_title}**"
                await message.edit(embed=embed)
            except Exception as e:
                print(f"Error updating radio message: {e}")
                break