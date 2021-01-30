import os
import asyncio
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


    def test(self):
        assert not os.getenv("BAN_URL") is None, \
            "BAN_URL is not defined"

        try:
            sample = discord.FFmpegPCMAudio(os.getenv("BAN_URL"))
        except:
            self.fail("Audio sample for etonmban could not be loaded")


    @commands.command()
    async def ban(self, ctx):
        """ Plays a nice audio sample in voice chat
        """
        if len(self.bot.voice_clients) > 0:
            return await ctx.send("I'm busy right now, try later...")

        if not ctx.author.voice:
            return await ctx.send("You must be in a voice chat to use this command!")

        channel = ctx.author.voice.channel
        self.voice_client = await channel.connect()

        sample = discord.FFmpegPCMAudio(os.getenv("BAN_URL"))
        self.voice_client.play(sample)

        await ctx.send("Et on m'ban!")

        while self.voice_client.is_playing():
            await asyncio.sleep(1)

        await self.voice_client.disconnect()

