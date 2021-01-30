import discord
import os
import modules

from dotenv import load_dotenv
from discord.ext import commands


class Z14(commands.Bot):
    def setup(self):
        # Topics can be used to listen/publish events across modules, it provides
        # easy and straightforward decoupling for modules
        self.listeners = {}

        self.modules = [
            modules.FeatureRequest(bot),
            modules.KickMalabar(bot),
            modules.KickPaglops(bot),
            modules.KickT4g1(bot),
            modules.Opinion(bot),
            modules.Ping(bot),
            modules.Popof(bot),
            modules.ScoreTracker(bot),
            modules.SoundEffects(bot),

            modules.AutoRole(bot),
            modules.SelfRole(bot),
        ]

        for module in self.modules:
            self.add_cog(module)

            if hasattr(module, "test"):
                module.test()


    async def subscribe(self, topic: str, listener: commands.Cog):
        """ Subscribe to an arbitrary topic
        """
        listeners = self.listeners.get(topic, [])
        listeners.append(listener)

        self.listeners[topic] = listeners


    async def publish(self, ctx: commands.Context, topic: str, value=None):
        """ Publish to an arbitrary topic
        """
        for listener in self.listeners.get(topic, []):
            if hasattr(listener, "on_topic_published"):
                await listener.on_topic_published(ctx, topic, value)


    def get_guild(self):
        """Return the main guild
        """
        return self.guilds[0]


    def test(self):
        assert len(self.guilds) == 1,  \
            "Connected to too many guilds, we support only one right now"

        assert not os.getenv("TOKEN") is None, \
            "TOKEN not found: Make sur you have a .env at z14 root"


    async def on_ready(self):
        """ Called when z14 is connected and ready to receive events
        """
        self.test()

        print("z14 is ready")


    async def give_role(self, member, role):
        print("Giving role {} to {}".format(
            role.name, member.name.encode("ascii", "ignore")))
        await member.add_roles(role)


    async def remove_role(self, member, role):
        print("Removing role {} from {}".format(
            role.name, member.name.encode("ascii", "ignore")))
        await member.remove_roles(role)


    async def remove_emoji(self, member, emoji, channel_id, message_id):
        """
        Removes an emoji from the given message
        """
        channel = self.get_guild().get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        await message.remove_reaction(emoji, member)


if __name__ == "__main__":
    load_dotenv()

    intents = discord.Intents.default()
    intents.reactions = True
    intents.members = True

    bot = Z14(command_prefix='.', intents=intents)

    bot.setup()

    bot.run(os.getenv("TOKEN"))
