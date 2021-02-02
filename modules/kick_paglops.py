import os
import discord

from discord.ext import commands


class KickPaglops(commands.Cog):
    """
    Embed a nice picture of the Paglops into the channel
    """
    def __init__(self, bot):
        self.bot = bot
        self.paglops = None
        self.paglops_url = os.getenv("PAGLOPS_URL")


    def test(self):
        assert not os.getenv("PAGLOPS_URL") is None, \
            "PAGLOPS_URL is not defined"
        assert not os.getenv("PAGLOPS_USER") is None, \
            "PAGLOPS_USER is not defined"


    def paglops_exist(ctx):
        """ Tell if paglops is on the server
        """
        return not ctx.cog.paglops is None


    @commands.Cog.listener()
    async def on_ready(self):
        paglops_name = os.getenv("PAGLOPS_USER", default="")
        self.paglops = self.bot.get_guild().get_member_named(paglops_name)


    @commands.command(name="kp")
    @commands.check(paglops_exist)
    async def kick_paglops(self, ctx):
        """ Send a nice picture of Paglops into the chan
        """
        embed = discord.Embed()
        embed.set_image(url=self.paglops_url)

        await ctx.send("Coucou {}".format(self.paglops.mention), embed=embed)


def setup(bot):
    bot.add_cog(KickPaglops(bot))


def teardown(bot):
    print('Reloading {}'.format('modules.kick_paglops'))
