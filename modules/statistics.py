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


def daycount(start_date, end_date):
    """ Number of days between two dates
    """
    return int((end_date - start_date).days) + 1


def daterange(start_date, end_date):
    """ Yiels every date between two given dates including start date
    """
    for n in range(daycount(start_date, end_date)):
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


    def is_voice_online(self, voice):
        """ Says if an user is online in voice chat
        """
        return voice and voice.channel and not voice.afk


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

            if self.is_voice_online(member.voice):
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


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Voice activity changed
        if self.is_voice_online(before) != self.is_voice_online(after):
            self.compute_member_uptime(VoiceActivity, member)


    @commands.command(name="stop")
    async def leaderboard(self, ctx):
        # Message sent per day
        sent_count = self.session.query(
            DailyResume.user_id,
            func.sum(DailyResume.message_count).label("sent_count")
        ).group_by(
            DailyResume.user_id
        ).order_by(
            func.sum(DailyResume.message_count).desc()
        ).limit(3)

        top_messages = ""
        for i in range(3):
            try:
                data = sent_count[i]
                user_name = self.bot.get_guild().get_member(data[0])
                score = data[1]
            except:
                user_name = "/"
                score = 0

            top_messages += "{} - {}\n".format(score, user_name)

        await ctx.send("```Leaderboard:\n" \
            "{}\n" \
            "```".format(
                top_messages
        ))


    @commands.command(name="suser")
    async def user_statistics(self, ctx, user_name):
        member = self.bot.get_guild().get_member_named(user_name)

        if not member:
            await ctx.send("Cet utilisateur n'a pas pu être trouvé. " \
                "Respectez le format suivant: " \
                "username#discriminator (test#0123)")
            return

        self.compute_all_uptime()

        today = datetime.combine(date.today(), datetime.min.time())

        month = today.replace(day=1)

        # Message sent per day
        sent_count = self.session.query(
            DailyResume.date,
            func.sum(DailyResume.message_count).label("sent_count")
        ).filter(
            DailyResume.user_id == member.id
        ).group_by(
            DailyResume.date
        ).order_by(
            DailyResume.date.asc()
        )

        # Total messages
        sum_sent_count = self.session.query(
            func.sum(sent_count.subquery().c.sent_count)
        ).scalar()

        if sum_sent_count == None:
            sum_sent_count = 0

        # Avearage message sent
        try:
            avg_sent_count = sum_sent_count / daycount(sent_count.first()[0], today)
        except TypeError:
            avg_sent_count = 0

        # Avearage message sent this month
        try:
            sum_sent_count_month = self.session.query(
                func.sum(
                    sent_count.filter(
                        DailyResume.date >= month
                    ).subquery().c.sent_count
                )
            ).scalar()
            avg_sent_count_month = sum_sent_count_month / daycount(month, today)
        except TypeError:
            avg_sent_count_month = 0

        await ctx.send("```Stats for user {}:\n" \
            "Messages sent total: {}\n" \
            "Average messages per day: {:.2f}\n" \
            "Average messages this month: {:.2f}```".format(
                member.name,
                sum_sent_count,
                avg_sent_count,
                avg_sent_count_month,
        ))


    @commands.command(name="stats")
    async def statistics(self, ctx):
        """ Provides somewhat useful statistics to users
        """
        self.compute_all_uptime()

        today = datetime.combine(date.today(), datetime.min.time())

        month = today.replace(day=1)

        # Chat online per day
        chat_online = self.session.query(
            DailyResume.date,
            func.count(DailyResume.user_id).label("chat_count")
        ).filter(
            DailyResume.chat_time > 0
        ).group_by(
            DailyResume.date
        ).order_by(
            DailyResume.date.asc()
        )

        # Message sent per day
        sent_count = self.session.query(
            DailyResume.date,
            func.sum(DailyResume.message_count).label("sent_count")
        ).group_by(
            DailyResume.date
        ).order_by(
            DailyResume.date.asc()
        )

        # Online users today
        chat_online_today = chat_online.filter(
            DailyResume.date == today).one()[1]

        # Messages sent today
        sent_count_today = sent_count.filter(
            DailyResume.date == today).one()[1]

        # Avearage daily online
        sum_chat_online = self.session.query(
            func.sum(chat_online.subquery().c.chat_count)
        ).scalar()
        avg_chat_online = sum_chat_online / daycount(chat_online.first()[0], today)

        # Avearage message sent
        sum_sent_count = self.session.query(
            func.sum(sent_count.subquery().c.sent_count)
        ).scalar()
        avg_sent_count = sum_sent_count / daycount(sent_count.first()[0], today)

        # Avearage message sent this month
        sum_sent_count_month = self.session.query(
            func.sum(
                sent_count.filter(
                    DailyResume.date >= month
                ).subquery().c.sent_count
            )
        ).scalar()
        avg_sent_count_month = sum_sent_count_month / daycount(month, today)

        # Total text online per users
        text_online = self.session.query(
            DailyResume.user_id,
            func.sum(DailyResume.chat_time).label("text_online")
        ).group_by(
            DailyResume.user_id
        )

        # Total voice online per users
        voice_online = self.session.query(
            DailyResume.user_id,
            func.sum(DailyResume.voice_time).label("voice_online")
        ).group_by(
            DailyResume.user_id
        )

        # Average time text online
        avg_text_online = self.session.query(
            func.avg(text_online.subquery().c.text_online)
        ).scalar()

        avg_text_online_month = self.session.query(
            func.avg(text_online.filter(
                    DailyResume.date >= month
                ).subquery().c.text_online
            )
        ).scalar()

        # Average time voice online
        avg_voice_online = self.session.query(
            func.avg(voice_online.subquery().c.voice_online)
        ).scalar()

        avg_voice_online_month = self.session.query(
            func.avg(voice_online.filter(
                    DailyResume.date >= month
                ).subquery().c.voice_online
            )
        ).scalar()

        z14_uptime = datetime.utcnow() - self.started_at

        # Sum of time spent online in voice by all users today
        sum_voice_online = self.session.query(
            func.sum(DailyResume.voice_time).label("voice_online")
        ).filter(
            DailyResume.date >= today
        ).scalar()

        # Sum of time spent online in voice by all users all time
        sum_voice_online_total = self.session.query(
            func.sum(DailyResume.voice_time).label("voice_online")
        ).scalar()

        await ctx.send("```There is {} users on the server!\n" \
            "Users online today: {}\n" \
            "Messages sent today: {}\n" \
            "Average users online per day: {:.2f}\n" \
            "Average messages per day: {:.2f}\n" \
            "Average messages this month: {:.2f}\n" \
            "z14 uptime: {}\n" \
            "Average time connected in text/day: {:.2f}s\n" \
            "Average time connected in voice/day: {:.2f}s\n" \
            "Average time connected in text/month: {:.2f}s\n" \
            "Average time connected in voice/month: {:.2f}s\n" \
            "Total time in voice today: {:.2f}s\n" \
            "Total time in voice: {:.2f}s```".format(
                len(ctx.guild.members),
                chat_online_today,
                sent_count_today,
                avg_chat_online,
                avg_sent_count,
                avg_sent_count_month,
                z14_uptime,
                avg_text_online,
                avg_voice_online,
                avg_text_online_month,
                avg_voice_online_month,
                sum_voice_online,
                sum_voice_online_total,
        ))


    @user_statistics.error
    async def error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("The following argument is missing: {}".format(
                error.param))

        else:
            print("Encountered unexpected error: {} {}".format(error, type(error)))
