import os
import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
from MusicBot import SerenadikBot

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = commands.Bot(command_prefix="!", help_command=None, intents=intents)

def ban_user(user_id):
    if user_id:
        SerenadikBot.ban_user(user_id)
        print(f"User with id '{ user_id }' has been banned.")

def unban_user(user_id):
    if user_id:
        SerenadikBot.unban_user(user_id)
        print(f"User with id '{ user_id }' has been unbanned.")

commands = {
    "/ban": lambda args: [ban_user(user_id) for user_id in args],
    "/unban": lambda args: [unban_user(user_id) for user_id in args]
}

async def main():
    try:
        await client.add_cog(SerenadikBot(client))
        await client.start(TOKEN)

    except Exception as e:
        print(e)
        return

async def async_input(prompt: str = ""):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, prompt)

async def io():
    print("Bot is active")
    while True:
        user_input = await async_input(": ")
        parts = user_input.split(" ")
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else None
        
        command_func = commands.get(command)
        if command_func:
            command_func(args)
        else:
            print("Unknown command")
        
async def run_async():
    await asyncio.gather(
        main(),
        io()
    )

if __name__ == "__main__":
    asyncio.run(run_async())