import os
import discord

from discord.ext import commands


class AutoRole(commands.Cog):
    """
    This class does the following:
    - For every new member: Give hm a predefined role
    - When restarted, check that every users has at least the pre-defined role
    """
    def __init__(self, bot):
        self.bot = bot
        self.role = None


    def test(self):
        assert not os.getenv("AUTO_ROLE") is None, "AUTO_ROLE is not defined"


    @commands.Cog.listener()
    async def on_ready(self):
        """
        Check every users has at least the role to them
        """
        auto_role = os.getenv("AUTO_ROLE", default="Joueur")

        self.role = discord.utils.get(
            self.bot.get_guild().roles, name=auto_role)

        if not self.role:
            raise Exception(
                "AUTO_ROLE not found! Create a role named {}".format(auto_role))

        for member in self.bot.get_guild().members:
            if len(member.roles) == 1:
                await self.bot.give_role(member, self.role)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        """ Gives new member a pre-defined role
        """
        await self.bot.give_role(member, self.role)


def setup(bot):
    bot.add_cog(AutoRole(bot))


def teardown(bot):
    print('Reloading modules.auto_role')
