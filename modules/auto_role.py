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


    @commands.Cog.listener()
    async def on_member_join(self, member):
        """ Gives new member a pre-defined role
        """
        auto_role = os.getenv("AUTO_ROLE", default="Joueur")

        role = discord.utils.get(member.guild.roles, name=auto_role)
        if role:
            await member.add_roles(role)
        else:
            print("AUTO_ROLE not found! Create a role named {}".format(auto_role))
