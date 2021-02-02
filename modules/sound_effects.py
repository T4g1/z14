import os
import logging
import asyncio
import discord

from discord.ext import commands

DRUM_SCORE_MAX = 5


class SoundEffects(commands.Cog):
    """
    Join the user in vocal to plays various sound effects
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None


    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.subscribe("score_tracker.scored", self)


    def test(self):
        assert not os.getenv("SFX_BAN_URL") is None, \
            "SFX_BAN_URL is not defined"
        assert not os.getenv("SFX_DRUM_URL") is None, \
            "SFX_DRUM_URL is not defined"

        try:
            sample = discord.FFmpegPCMAudio(os.getenv("SFX_BAN_URL"))
            sample = discord.FFmpegPCMAudio(os.getenv("SFX_DRUM_URL"))
        except:
            self.fail("Some audio sample could not be loaded, check config")


    async def on_topic_published(self, ctx, topic, value):
        """ Module scored_tracker scored some points
        """
        if value > DRUM_SCORE_MAX:
            return

        await self.drum(ctx)


    @commands.command()
    async def ban(self, ctx):
        """ Plays the "Et on m'ban" sound effect
        """
        await self.sound_effect(ctx, os.getenv("SFX_BAN_URL"), "Et on m'ban!")


    @commands.command()
    async def drum(self, ctx):
        """ Plays the "Ba dum tss" sound effect
        """
        await self.sound_effect(ctx, os.getenv("SFX_DRUM_URL"), "Ba dum tsss")


    async def sound_effect(self, ctx, sfx_url, message):
        """ Plays the given sound effect URL
        """
        if len(self.bot.voice_clients) > 0:
            return await ctx.send("I'm busy right now, try later...")

        if not ctx.author.voice:
            return await ctx.send(
                "You must be in a voice chat to use this command!")

        channel = ctx.author.voice.channel
        self.voice_client = await channel.connect()

        sample = discord.FFmpegPCMAudio(sfx_url)
        self.voice_client.play(sample)

        await ctx.send(message)

        while self.voice_client.is_playing():
            await asyncio.sleep(1)

        await asyncio.sleep(1)
        await self.voice_client.disconnect()


def setup(bot):
    bot.add_cog(SoundEffects(bot))


def teardown(bot):
    logging.info('Reloading modules.sound_effects')
