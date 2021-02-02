import os

from discord.ext import commands


class KickT4g1(commands.Cog):
    """
    Every time the command is invoked, it tells the user to go fuck itslef
    """
    def __init__(self, bot):
        self.bot = bot


    def test(self):
        pass


    @commands.command(name="kt")
    async def kick_t4g1(self, ctx):
        """ Tells the user to go fuck itself
        """
        await ctx.send("Dans tes rêves {}".format(ctx.author.mention))
        await ctx.author.send("*Fear the wrath of T4g1*")


def setup(bot):
    bot.add_cog(KickT4g1(bot))


def teardown(bot):
    print('Reloading {}'.format('modules.kick_t4g1'))
