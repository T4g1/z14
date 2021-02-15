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

# Duration of a poll in days
POLL_LIFESPAN = 2

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


class Polls(Base):
    """ Save every polls made and who made them
    """
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer)
    channel_id = Column(Integer)
    vote_msg_id = Column(Integer)
    result_msg_id = Column(Integer)

    when = Column(DateTime, default=datetime.utcnow)


class Options(Base):
    """ One option for a poll
    """
    __tablename__ = "options"

    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey('polls.id'))

    poll = relationship("Polls", back_populates="options")

    value = Column(String)
    emote = Column(String)


class Poll(commands.Cog):
    """
    Allow users to starts polling other users
    """
    def __init__(self, bot):
        self.bot = bot

        Session = sessionmaker(bind=self.bot.engine)
        self.session = Session()

        Polls.options = relationship("Options", back_populates="poll")

        Base.metadata.create_all(self.bot.engine)


    def test(self):
        pass


    @commands.Cog.listener()
    async def on_ready(self):
        active_polls = self.session.query(Polls).filter(
            Polls.when <= Polls.when + timedelta(days=POLL_LIFESPAN)
        ).all()

        for poll in active_polls:
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
        end = poll.when + timedelta(days=POLL_LIFESPAN)
        if datetime.utcnow() >= end:
            return

        channel = self.bot.get_guild().get_channel(poll.channel_id)
        vote_message = await channel.fetch_message(poll.vote_msg_id)
        result_message = await channel.fetch_message(poll.result_msg_id)

        reactions = vote_message.reactions

        # Filter and sort results
        results = []
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

            if count <= 0:
                continue

            results.append((option.emote, count))

        # Construct results message
        content = ">>> Total votes: {}\n".format(len(reactions))
        for result in sorted(results, key=lambda result: result[1]):
            content += "{} {}\n".format(result[0], result[1])

        content += "Poll ends {}".format(
            self.bot.print_time(end)
        )

        await result_message.edit(content=content)


    @commands.command(name="pd")
    async def delete_poll(self, ctx, *args):
        """ Remove last poll from the user
        """
        poll = self.session.query(Polls).filter(
            Polls.user_id == ctx.author.id
        ).order_by(Polls.when.desc()).first()
        if not poll:
            await ctx.send("No poll to delete")
            return

        # Remove both messages
        channel = self.bot.get_guild().get_channel(poll.channel_id)
        vote_message = await channel.fetch_message(poll.vote_msg_id)
        result_message = await channel.fetch_message(poll.result_msg_id)

        await vote_message.delete()
        await result_message.delete()

        for option in poll.options:
            option.delete()

        poll.delete()
        self.session.commit()


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

        vote_message = await ctx.send(self.create_vote_message(title, options))
        result_message = await ctx.send(">>> Total votes: 0\n")

        # Save the poll details
        poll = Polls(
            user_id=ctx.author.id,
            channel_id = ctx.channel.id,
            vote_msg_id = vote_message.id,
            result_msg_id = result_message.id
        )
        self.session.add(poll)
        self.session.commit()

        for option in options:
            option.poll_id = poll.id
            self.session.add(option)

        self.session.commit()

        # Make the result message
        await self.update_poll(poll)


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

        return ">>> {}\n{}".format(title, "\n".join(options_messages))


def setup(bot):
    bot.add_cog(Poll(bot))

