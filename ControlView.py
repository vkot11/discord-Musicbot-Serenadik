import discord

class SerenadikView(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=None)  # timeout=None означає, що кнопки не зникнуть
        self.bot = bot
        self.ctx = ctx

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.primary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            # self.ctx.voice_client.stop()
            # await interaction.response.send_message("The song is skipped ⏭", ephemeral=True)
            await interaction.response.defer()
            await self.bot.loop.create_task(self.bot.cogs['SerenadikBot'].skip(self.ctx))

    @discord.ui.button(label="⏯️ Pause | Resume", style=discord.ButtonStyle.success)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            await interaction.response.send_message("The song is paused ⏸️", ephemeral=True)
        
        elif self.ctx.voice_client and not self.ctx.voice_client.is_playing():
            self.ctx.voice_client.resume()
            await interaction.response.send_message("The song continues to play ⏯️", ephemeral=True)

    @discord.ui.button(label="🛑 Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.ctx.voice_client:
            self.bot.cogs['SerenadikBot'].get_queue(self.ctx.guild).clear()
            self.ctx.voice_client.stop()
            await interaction.response.send_message("Stopped the music and cleared the queue 🛑", ephemeral=False)
            
