import discord

class SerenadikView(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=None)  # timeout=None означає, що кнопки не зникнуть
        self.bot = bot
        self.ctx = ctx

    @discord.ui.button(label="⏮ Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.ctx.voice_client:
            await interaction.response.defer()
            await self.bot.cogs['SerenadikBot'].previous(self.ctx)

    @discord.ui.button(label="⏯️ Pause | Resume", style=discord.ButtonStyle.success)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):

# testing bugs
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None
        bot_voice_channel = interaction.guild.voice_client.channel if interaction.guild.voice_client else None

        if not voice_channel or voice_channel != bot_voice_channel:
            await interaction.response.send_message("You are loser", ephemeral=True)
            return

        if not self.ctx.voice_client:
            return

        if self.ctx.voice_client.is_playing():
            await self.bot.cogs['SerenadikBot'].pause(self.ctx)
            message = "The song is paused ⏸️"
        else:
            await self.bot.cogs['SerenadikBot'].resume(self.ctx)
            message = "The song continues to play ⏯️"
        
        await interaction.response.send_message(message, ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.primary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            await interaction.response.defer()
            await self.bot.cogs['SerenadikBot'].skip(self.ctx)

    @discord.ui.button(label="🔀 Shuffle", style=discord.ButtonStyle.secondary)
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.ctx.voice_client:
            return

        if self.ctx.voice_client.is_playing():
            await interaction.response.defer()
            await self.bot.cogs['SerenadikBot'].shuffle(self.ctx)

    @discord.ui.button(label="🔄 Loop", style=discord.ButtonStyle.secondary)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.ctx.voice_client:
            return

        if self.ctx.voice_client.is_playing():
            await interaction.response.defer()
            await self.bot.cogs['SerenadikBot'].loop(self.ctx)

    @discord.ui.button(label="🛑 Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client:
            await interaction.response.defer()
            await self.bot.cogs['SerenadikBot'].stop(self.ctx)
            