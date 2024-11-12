import asyncio
import discord
from discord.ext import commands
from MusicBot import SerenadikBot
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = commands.Bot(command_prefix="!", intents=intents)

async def main():
    try:
        await client.add_cog(SerenadikBot(client))
        await client.start(TOKEN)
    except Exception as e:
        print(e)
        return

if __name__ == "__main__":
    asyncio.run(main())