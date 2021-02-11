import os
import discord

from discord.ext import commands
from datetime import date, datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, aliased, relationship
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Integer,
    DateTime,
    or_
)

Base = declarative_base()


MULTI_CHOICE_EMOTES = [
    "\U00000031\U0000FE0F\U000020E3",
    "\U00000032\U0000FE0F\U000020E3",
    "\U00000033\U0000FE0F\U000020E3",
    "\U00000034\U0000FE0F\U000020E3",
    "\U00000035\U0000FE0F\U000020E3",
    "\U00000036\U0000FE0F\U000020E3",
    "\U00000037\U0000FE0F\U000020E3",
    "\U00000038\U0000FE0F\U000020E3",
    "\U00000039\U0000FE0F\U000020E3",
    "\U0001F51F",
]


class PollOption():
    def __init__(self, name, emote):
        self.name = name
        self.emote = emote


class Options(Base):
    """ One option for a poll
    """
    __tablename__ = "options"

    id = Column(Integer, primary_key=True)

    poll = Column(Integer, ForeignKey("polls.id"))

    value = Column(String)
    emote = Column(String)


class Polls(Base):
    """ Save every polls made and who made them
    """
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True)
    options = relationship("Options")

    user_id = Column(Integer)
    channel_id = Column(Integer)
    vote_msg_id = Column(Integer)
    result_msg_id = Column(Integer)

    when = Column(DateTime, default=datetime.utcnow)


class Poll(commands.Cog):
    """
    Allow users to starts polling other users
    """
    def __init__(self, bot):
        self.bot = bot

        Session = sessionmaker(bind=self.bot.engine)
        self.session = Session()

        Base.metadata.create_all(self.bot.engine)


    def test(self):
        pass


    @commands.Cog.listener()
    async def on_ready(self):
        for poll in self.session.query(Polls).all():
            await self.clean_reactions(poll)
            await self.update_poll(poll)


    async def clean_reactions(self, poll):
        """ Clean wrong emoji on polls
        """
        channel = self.bot.get_guild().get_channel(poll.channel_id)
        vote_message = await channel.fetch_message(poll.vote_msg_id)
        result_message = await channel.fetch_message(poll.result_msg_id)

        for reaction in result_message.reactions:
            users = await reaction.users().flatten()
            for user in users:
                reaction.remove(user)

        for reaction in vote_message.reactions:
            if self.is_poll_option(poll, reaction.emoji):
                continue

            users = await reaction.users().flatten()
            for user in users:
                reaction.remove(user)


    async def update_poll(self, poll):
        """ Update poll stats based on emojis
        """
        channel = self.bot.get_guild().get_channel(poll.channel_id)
        vote_message = await channel.fetch_message(poll.vote_msg_id)
        result_message = await channel.fetch_message(poll.result_msg_id)

        reactions = vote_message.reactions
        content = ""

        for option in poll.options:
            option_reaction = None
            for reaction in vote_message.reactions:
                if self.get_emoji_name(reaction.emoji) == option.emote:
                    option_reaction = reaction
                    break

            if option_reaction == None:
                count = 0
            else:
                users = await option_reaction.users().flatten()
                count = len(users)

            content += "{} {}\n".format(option.emote, count)

        content += "Max: {}\n".format(len(reactions))

        await result_message.edit(content=content)


    @commands.command(name="poll")
    async def create_poll(self, ctx, *args):
        """ Starts a poll
        """
        if len(args) <= 0:
            await ctx.send("Wrong command format: " \
                "You need to at least specify a question")
            return

        title = args[0]

        options = []

        # Too many choices
        if len(args[1:]) > len(MULTI_CHOICE_EMOTES):
            await ctx.send("There is too many choice in that poll, " \
                "limite yourself to {} options!".format(
                    len(MULTI_CHOICE_EMOTES)
            ))
            return

        # Create all options
        for i in range(len(args[1:])):
            option = args[i + 1]
            emote = MULTI_CHOICE_EMOTES[i]

            options.append(Options(value=option, emote=emote))

        # Yes/No poll
        if len(options) <= 0:
            option1 = Options(value="Yes", emote="\U00002705")
            option2 = Options(value="No", emote="\U0000274C")

            options = [ option1, option2]

        poll = self.bot.get_or_create(self.session, Polls,
            user_id = ctx.author.id
        )

        vote_message = await ctx.send(self.create_vote_message(title, options))
        result_message = await ctx.send("Result message")

        # Save the poll details
        poll.channel_id = ctx.channel.id
        poll.vote_msg_id = vote_message.id
        poll.result_msg_id = result_message.id

        for option in options:
            option.poll = poll.id
            self.session.add(option)

        self.session.commit()


    def get_poll(self, message_id):
        """" Get the poll related to given message ID
        """
        return self.session.query(Polls).filter(
            or_(
                Polls.vote_msg_id == message_id,
                Polls.result_msg_id == message_id
            )
        ).first()


    def get_emoji_name(self, emoji):
        """ Extract name of an emoji
        """
        emoji_name = emoji
        if type(emoji) != str:
            emoji_name = emoji.name

        return emoji_name


    def is_poll_option(self, poll, emoji):
        """ Tells wether or not this emoji can be used on this poll
        """
        emoji_name = self.get_emoji_name(emoji)

        for option in poll.options:
            if emoji_name == option.emote:
                return True

        return False


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        poll = self.get_poll(payload.message_id)
        if poll is None:
            return

        # Not the correct message or not an option
        remove_emoji = not self.is_poll_option(poll, payload.emoji)
        remove_emoji = remove_emoji or payload.message_id != poll.vote_msg_id

        if remove_emoji:
            member = self.bot.get_guild().get_member(payload.user_id)

            await self.bot.remove_emoji(
                member, payload.emoji, payload.channel_id, payload.message_id
            )
            return

        await self.update_poll(poll)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        poll = self.get_poll(payload.message_id)
        if poll is None:
            return

        # Not a valid option
        if not self.is_poll_option(poll, payload.emoji):
            return

        await self.update_poll(poll)


    def create_vote_message(self, title, options):
        """ Create the message for the voting message
        """
        options_messages = []
        for option in options:
            options_messages.append("{} {}".format(option.emote, option.value))

        return "{}\n{}".format(title, "\n".join(options_messages))


def setup(bot):
    bot.add_cog(Poll(bot))
