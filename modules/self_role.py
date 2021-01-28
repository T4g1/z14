import os
import discord

from discord.ext import commands


class SelfRole(commands.Cog):
    """
    This class does the following given a message ID on the server:
    - For every reaction on the message, it assign a role to the users
     who have reacted to the message.
     - A mapping of emojis <-> Role can be configured
    - Re-assign those roles when restarted: Check that every users on the guild
     have the role only if they have reacted to said message
    """
    def __init__(self, bot):
        self.bot = bot
        self.message_id = 0
        self.roles_mapping = {}


    @commands.Cog.listener()
    async def on_ready(self):
        self.message_id = self.get_role_message_id()
        self.extract_roles_mapping()


    def get_role_message_id(self):
        """Gives the ID of the message used to allow users to select their roles
        """
        try:
            message_id = os.getenv("ROLE_MESSAGE_ID", default="0")
            return int(message_id)
        except Exception as e:
            raise Exception("Error while trying to read ROLE_MESSAGE_ID, \
                make sure it's defined and it is an integer")


    def extract_roles_mapping(self):
        """ Extract mapping of emoji to role to assign roles to users
        that add the emoji to the message with ID ROLE_MESSAGE_ID
        """
        raw_mapping = os.getenv("ROLE_EMOJIS", default="")

        self.roles_mapping = {}

        try:
            raw_mappings = raw_mapping.split(";")

            for raw_mapping in raw_mappings:
                if raw_mapping == "":
                    continue

                emoji, role_name = raw_mapping.split(",")

                role = discord.utils.get(
                    self.bot.get_guild().roles, name=role_name)

                if not role:
                    print("Role {} not found on that server, ignored".format(
                        role_name
                    ))
                    continue

                self.roles_mapping[emoji] = role
        except Exception as e:
            raise Exception("ROLE_EMOJIS is badly formatted: \
                :[EMOJI 1]:,[ROLE 1];:[EMOJI 2]:,[ROLE 2]")

        print("Self role feature has loaded the following roles: ")
        print(self.roles_mapping)


    async def manage_role(self, payload, remove=False):
        """
        Analyse the payload's emoji to determine which role to add or remove
        """
        member = self.bot.get_guild().get_member(payload.user_id)

        if not payload.emoji.name in self.roles_mapping.keys():
            if remove:
                return

            # Remove the emoji
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
            return

        role = self.roles_mapping[payload.emoji.name]

        if remove:
            await member.remove_roles(role)

            print("Removing role {} from {}".format(
                role.name, member.name
            ))
        else:
            await member.add_roles(role)

            print("Adding role {} to {}".format(
                role.name, member.name
            ))


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.message_id:
            return

        await manage_role(payload, remove=False)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id != self.message_id:
            return

        await manage_role(payload, remove=True)


