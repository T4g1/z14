import os

from discord.ext import commands


class KickMalabar(commands.Cog):
    """
    Command that will mute Malabar
    """
    def __init__(self, bot):
        self.bot = bot


    def test(self):
        assert not os.getenv("MALABAR") is None, "MALABAR is not defined"


    @commands.command(name="km")
    async def kick_malabar(self, ctx):
        """ Mute Malabar
        """
        malabar_name = os.getenv("MALABAR", default="")
        if not malabar_name:
            print("You have'nt configured a malabar username")
            return

        malabar = ctx.guild.get_member_named(malabar_name)
        if not malabar:
            await ctx.send("Il est parti du serveur :'(".format(malabar_name))
        else:
            await ctx.send("{} TAGEULE".format(malabar.mention))
