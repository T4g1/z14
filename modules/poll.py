import os
import discord

from discord.ext import commands
from datetime import date, datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
)

Base = declarative_base()


class Polls(Base):
    """ Save every polls made and who made them
    """
    __tablename__ = "polls"

    user_id = Column(Integer, primary_key=True)
    vote_msg_id = Column(Integer, primary_key=True)
    result_msg_id = Column(Integer, primary_key=True)

    when = Column(DateTime, primary_key=True, default=datetime.utcnow)


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
        pass


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
        for option in args[1:]:
            options.append(option)

        # Yes/No poll
        if len(options) <= 0:
            options = [
                "Yes",
                "No"
            ]

        vote_message = await ctx.send(self.create_vote_message(title, options))
        result_message = await ctx.send("Result message")

        poll = self.bot.get_or_create(self.session, Polls,
            user_id = ctx.author.id,
            vote_msg_id = vote_message.id,
            result_msg_id = result_message.id,
        )


    def create_vote_message(self, title, options):
        """ Create the message for the voting message
        """
        return "{}\n{}".format(title, "\n".join(options))


def setup(bot):
    bot.add_cog(Poll(bot))

