import os
import discord


from discord.ext import commands


class Opinion(commands.Cog):
    """
    Command that will mute Malabar
    """

    def __init__(self, bot):
        self.bot = bot
        self.opinion_url = os.getenv("OPINION_URL")

    def test(self):
        assert (
            not os.getenv("OPINION_URL") is None
        ), "OPINION_URL is not defined"

    @commands.command(name="o")
    async def opinion(self, ctx):
        """Embed an opinion into the channel"""
        embed = discord.Embed()
        embed.set_image(url=self.opinion_url)

        await ctx.send(embed=embed)

    @opinion.error
    async def error_handler(self, ctx, error):
        print(
            "Encountered unexpected error: {} {}".format(error, type(error))
        )


async def setup(bot):
    await bot.add_cog(Opinion(bot))
