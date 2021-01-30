import os
import discord

from discord.ext import commands


class Popof(commands.Cog):
    """
    Embed a nice picture of an popsicle
    """
    def __init__(self, bot):
        self.bot = bot


    def test(self):
        assert not os.getenv("POPOF_URL") is None, \
            "POPOF_URL is not defined"
        assert not os.getenv("POPOF_CHANNEL") is None, \
            "POPOF_CHANNEL is not defined"

        try:
            channel_id = int(os.getenv("POPOF_CHANNEL"))
        except:
            self.fail("Channel ID must be an integer")


    async def is_irc_channel(ctx):
        """ Check that this is the correct channel
        """
        return ctx.channel.id == int(os.getenv("POPOF_CHANNEL"))


    @commands.command(name="bp")
    @commands.check(is_irc_channel)
    async def popof_pick(self, ctx):
        """ Send a nice picture of an icicle in the chat
        """
        embed = discord.Embed()
        embed.set_image(url=os.getenv("POPOF_URL"))

        channel = self.bot.get_guild().get_channel(
            int(os.getenv("POPOF_CHANNEL")))

        await channel.send("Coucou tu veux voir ma glace ?", embed=embed)
