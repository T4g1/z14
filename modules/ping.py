from discord.ext import commands

class Ping(commands.Cog):
    """
    Simple ping/pong command
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """ Reply pong to every ping command
        """
        await ctx.send('pong')


def setup(bot):
    bot.add_cog(Ping(bot))


def teardown(bot):
    print('Reloading {}'.format('modules.ping'))
