import discord
import os
import asyncpraw

from cogwatch import watch
from dotenv import load_dotenv
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


class Z14(commands.Bot):
    def setup(self):
        # Topics can be used to listen/publish events across modules, it provides
        # easy and straightforward decoupling for modules
        self.listeners = {}

        self.test()

        try:
            self.reddit = asyncpraw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent=os.getenv("REDDIT_AGENT")
            )
        except Exception as e:
            print(e)
            self.reddit = None

        self.engine = create_engine(
            os.getenv("DB_PATH", default="sqlite:///data.db"))

        self.Base = declarative_base()

        self.modules = [
            'modules.auto_role',
            'modules.feature_request',
            'modules.hydrohomies',
            'modules.kick_malabar',
            'modules.kick_paglops',
            'modules.kick_t4g1',
            'modules.opinion',
            'modules.ping',
            'modules.popof',
            'modules.score_tracker',
            'modules.self_role',
            'modules.sound_effects',
            'modules.statistics',
        ]

        self.Base.metadata.create_all(self.engine)

        for module in self.modules:
            self.load_extension(module)

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
        assert not os.getenv("TOKEN") is None, \
            "TOKEN not found: Make sur you have a .env at z14 root"
        assert not os.getenv("DB_PATH") is None, \
            "DB_PATH not found"

        """
        # Optionnal parameters
        assert not os.getenv("REDDIT_CLIENT") is None, \
            "REDDIT_CLIENT not found"
        assert not os.getenv("REDDIT_SECRET") is None, \
            "REDDIT_SECRET not found"
        assert not os.getenv("REDDIT_AGENT") is None, \
            "REDDIT_AGENT not found"
        """


    @watch(path='modules')
    async def on_ready(self):
        """ Called when z14 is connected and ready to receive events
        """
        assert len(self.guilds) == 1,  \
            "Connected to too many guilds, we support only one right now"

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


    def get_or_create(self, session, model, **kwargs):
        """ Get data from a model and create it if it does not exist
        """
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            session.add(instance)
            session.commit()
            return instance


if __name__ == "__main__":
    load_dotenv()

    intents = discord.Intents.all()

    bot = Z14(command_prefix='.', intents=intents)

    bot.setup()

    bot.run(os.getenv("TOKEN"))
