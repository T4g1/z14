import pandas as pd
import os
import discord
import sqlalchemy

from discord.ext import commands
from datetime import date, datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import (
    Column,
    Date,
    Integer,
    Boolean,
    String,
    DateTime,
    cast,
    desc,
    distinct,
    func,
    and_
)

Base = declarative_base()


def daterange(start_date, end_date):
    """ Yiels every date between two given dates including start date
    """
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


class VoiceActivity(Base):
    """ Tracking: Daily voice chat activity
    Each row is one user being online from that point in time
    """
    __tablename__ = "stats_voice_activity"

    datetime = Column(DateTime, primary_key=True, default=datetime.utcnow)
    user_id = Column(Integer, primary_key=True)


class TextActivity(Base):
    """ Tracking: Daily chat activity
    Each row is one user being online from that point in time
    """
    __tablename__ = "stats_text_activity"

    datetime = Column(DateTime, primary_key=True, default=datetime.utcnow)
    user_id = Column(Integer, primary_key=True)


class DailyResume(Base):
    """ Historical: computed from tracking tables
    """
    __tablename__ = "stats_daily_resume"

    date = Column(DateTime, primary_key=True, default=date.today)
    user_id = Column(Integer, primary_key=True)

    message_count = Column(Integer, default=0)
    chat_time = Column(Integer, default=0)
    voice_time = Column(Integer, default=0)


class Statistics(commands.Cog):
    """
    Provide various statistics
    """
    # TODO: Catch going offline
    # TODO: Compute uptimes periodically
    def __init__(self, bot):
        self.bot = bot
        self.started_at = datetime.utcnow()

        Session = sessionmaker(bind=self.bot.engine)
        self.session = Session()

        Base.metadata.create_all(self.bot.engine)


    def test(self):
        pass


    def is_text_online(self, member):
        """ Says if an user is online in text chat
        """
        return member.status == discord.Status.online


    def is_voice_online(self, member):
        """ Says if an user is online in voice chat
        """
        return member.voice and not member.voice.afk


    @commands.Cog.listener()
    async def on_ready(self):
        """ Bot goes online
        """
        # Delete all tracking left
        self.session.query(TextActivity).delete()
        self.session.query(VoiceActivity).delete()

        self.check_online()


    def check_online(self):
        """ For every online member in text/voice:
        Adds an entry into TRACKING data
        """
        for member in self.bot.get_guild().members:
            if self.is_text_online(member):
                self.track_text_activity(member)

            if self.is_voice_online(member):
                self.track_voice_activity(member)


    def compute_all_uptime(self):
        """ Update uptime data for every users
        """
        # Text
        for row in self.session.query(TextActivity):
            member = self.bot.get_guild().get_member(row.user_id)

            self.compute_member_uptime(TextActivity, member)

        # Voice
        for row in self.session.query(VoiceActivity):
            member = self.bot.get_guild().get_member(row.user_id)

            self.compute_member_uptime(VoiceActivity, member)


    def compute_member_uptime(self, model, member):
        """ Compute uptime for a particular user
        """
        tracking = self.session.query(model).filter(
            model.user_id == member.id
        ).first()

        if not tracking:
            # Create tracking information
            if model == TextActivity:
                self.track_text_activity(member)
            else:
                self.track_voice_activity(member)

            return

        last_online = tracking.datetime
        for current_date in daterange(tracking.datetime.date(), date.today()):
            uptime = 0

            # The day processed is today
            if current_date == date.today():
                uptime = datetime.utcnow() - last_online
            # The day processed is a previous day
            else:
                uptime = timedelta(days=1) - last_online

            last_online = timedelta(days=0)

            # Update daily resume uptime for that day
            historical = self.get_daily_default(member, current_date)

            if model == TextActivity:
                historical.chat_time += uptime.total_seconds()
            else:
                historical.voice_time += uptime.total_seconds()

            self.session.commit()

        # Update row time
        if self.is_text_online(member):
            tracking.datetime = datetime.utcnow()
        # Delete row
        else:
            self.session.delete(tracking)

        self.session.commit()


    def track_text_activity(self, member):
        """ Record when a user becomes online in text
        """
        self.track_activity(TextActivity, member)


    def track_voice_activity(self, member):
        """ Record when a user becomes online in voice
        """
        self.track_activity(VoiceActivity, member)


    def track_activity(self, model, member):
        """ Generic activity tracking update
        """
        activity = model(
            datetime=datetime.utcnow(),
            user_id=member.id
        )
        self.session.add(activity)
        self.session.commit()


    def get_daily_default(self, member, date=date.today()):
        """ Get the member/day historical record
        """
        date = datetime.combine(date, datetime.min.time())

        return self.bot.get_or_create(self.session, DailyResume,
            date=date,
            user_id=member.id
        )


    @commands.Cog.listener()
    async def on_message(self, message):
        """
        When we receive a message
        """
        row = self.get_daily_default(message.author)
        row.message_count += 1

        self.session.commit()


    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Text activity changed
        if self.is_text_online(before) != self.is_text_online(after):
            self.compute_member_uptime(TextActivity, after)

        # Voice activity changed
        if self.is_voice_online(before) != self.is_voice_online(after):
            self.compute_member_uptime(VoiceActivity, after)


    @commands.command(name="stats")
    async def statistics(self, ctx):
        """ Provides somewhat useful statistics to users
        """
        self.compute_all_uptime()

        today = datetime.combine(date.today(), datetime.min.time())

        # TODO: All queries should have one day even when no activity is recorded that day

        # Chat online per day
        chat_online = self.session.query(
            DailyResume.date,
            func.count(DailyResume.user_id).label("chat_count")
        ).filter(
            DailyResume.chat_time > 0
        ).group_by(
            DailyResume.date
        )

        # Message sent per day
        sent_count = self.session.query(
            DailyResume.date,
            func.sum(DailyResume.message_count).label("sent_count")
        ).group_by(
            DailyResume.date
        )

        # Online users today
        chat_online_today = chat_online.filter(
            DailyResume.date == today).one()[1]

        # Messages sent today
        sent_count_today = sent_count.filter(
            DailyResume.date == today).one()[1]

        # Avearage daily online
        avg_chat_online = self.session.query(
            func.avg(chat_online.subquery().c.chat_count)
        ).scalar()

        # Avearage message sent
        avg_sent_count = self.session.query(
            func.avg(sent_count.subquery().c.sent_count)
        ).scalar()

        await ctx.send("```There is {} users on the server!\n" \
            "Users online today: {}\n" \
            "Messages sent today: {}\n" \
            "Average users online per day: {:.2f}\n" \
            "Average messages per day: {:.2f}```".format(
                len(ctx.guild.members),
                chat_online_today,
                sent_count_today,
                avg_chat_online,
                avg_sent_count,
        ))
