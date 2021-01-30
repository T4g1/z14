import os
import discord

from discord.ext import commands


class EtOnMBan(commands.Cog):
    """
    Join the user in vocal to play the "et on m'ban" sample
    """
    def __init__(self, bot):
        self.bot = bot
        self.ban_url = os.getenv("BAN_URL")
        self.voice_client = None
        self.sample = discord.FFmpegPCMAudio(os.getenv("BAN_URL"))


    def test(self):
        assert not os.getenv("BAN_URL") is None, \
            "BAN_URL is not defined"

        assert discord.FFmpegPCMAudio(os.getenv("BAN_URL")), \
            "Audio sample for etonmban could not be loaded"


    async def on_play_end(error):
        """ Disconnects bot from voice channel
        """
        if not self.voice_client:
            return

        await self.voice_client.disconnect()


    @commands.command()
    async def ban(self, ctx):
        """ Plays a nice audio sample in voice chat
        """
        if not ctx.author.voice:
            pass #return await ctx.send("You must be in a voice chat to use this command!")

        # DEBUG
        channel = self.bot.get_channel(804323830696640527) #ctx.author.voice.channel
        self.voice_client = await channel.connect()

        self.voice_client.play(self.sample, on_play_end)

