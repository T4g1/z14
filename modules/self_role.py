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
        self.channel_id = 0
        self.message_id = 0
        self.roles_mapping = {}


    def test(self):
        assert not os.getenv("ROLE_MESSAGE_ID") is None, \
            "ROLE_MESSAGE_ID is not defined"
        assert not os.getenv("ROLE_CHANNEL_ID") is None, \
            "ROLE_CHANNEL_ID is not defined"
        assert not os.getenv("ROLE_EMOJIS") is None, "ROLE_EMOJIS is not defined"

        try:
            message_id = int(os.getenv("ROLE_MESSAGE_ID", default="0"))
        except Exception as e:
            self.fail("ROLE_MESSAGE_ID is not an integer")

        try:
            message_id = int(os.getenv("ROLE_CHANNEL_ID", default="0"))
        except Exception as e:
            self.fail("ROLE_CHANNEL_ID is not an integer")


    @commands.Cog.listener()
    async def on_ready(self):
        self.channel_id = self.get_channel_id()
        self.message_id = self.get_message_id()
        self.extract_roles_mapping()

        channel = self.bot.get_guild().get_channel(self.channel_id)
        message = await channel.fetch_message(self.message_id)

        # Remove non wanted emojis from role message
        for message_reaction in message.reactions:
            if not message_reaction.emoji.name in self.roles_mapping.keys():
                users = await message_reaction.users().flatten()

                for member in users:
                    await self.bot.remove_emoji(
                        member,
                        message_reaction.emoji,
                        message.channel.id,
                        message.id
                    )
                break

        for emoji, role in self.roles_mapping.items():
            # Check the reaction corresponding to that emoji on the message
            users = []
            for message_reaction in message.reactions:
                if message_reaction.emoji.name == emoji:
                    users = await message_reaction.users().flatten()
                    break

            for member in self.bot.get_guild().members:
                # User have the role but has not reacted
                if role in member.roles:
                    if not member in users:
                       await self.bot.remove_role(member, role)
                # User does not have the role but has reacted
                else:
                    if member in users:
                        await self.bot.give_role(member, role)


    def get_channel_id(self):
        """Gives the ID of the channel used to allow users to select their roles
        """
        return int(os.getenv("ROLE_CHANNEL_ID", default="0"))


    def get_message_id(self):
        """Gives the ID of the message used to allow users to select their roles
        """
        return int(os.getenv("ROLE_MESSAGE_ID", default="0"))


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
                        role_name.encode("ascii", "ignore")
                    ))
                    continue

                self.roles_mapping[emoji] = role
        except Exception as e:
            raise Exception("ROLE_EMOJIS is badly formatted: \
                :[EMOJI 1]:,[ROLE 1];:[EMOJI 2]:,[ROLE 2]")

        print("Self role feature has loaded the following roles: ")
        for emoji, role in self.roles_mapping.items():
            print(":{}: to {}".format(
                emoji.encode("ascii", "ignore"),
                role.name.encode("ascii", "ignore")
            ))


    async def process_reaction(self, payload, remove=False):
        """
        Analyse the payload's emoji to determine which role to add or remove
        """
        member = self.bot.get_guild().get_member(payload.user_id)

        if not payload.emoji.name in self.roles_mapping.keys():
            if remove:
                return

            await self.bot.remove_emoji(
                member, payload.emoji, payload.channel_id, payload.message_id)
            return

        role = self.roles_mapping[payload.emoji.name]

        if remove:
            await self.bot.remove_role(member, role)
        else:
            await self.bot.give_role(member, role)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.message_id:
            return

        await self.process_reaction(payload, remove=False)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id != self.message_id:
            return

        await self.process_reaction(payload, remove=True)


