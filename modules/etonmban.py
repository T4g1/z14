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


    def test(self):
        assert not os.getenv("BAN_URL") is None, \
            "BAN_URL is not defined"


    @commands.command()
    async def ban(self, ctx):
        """ Plays a nice audio sample in voice chat
        """
        pass
