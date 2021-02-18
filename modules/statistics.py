from discord.ext import commands
from datetime import date, datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    func,
    and_,
)

Base = declarative_base()


def date_to_datetime(date):
    """Gives the datetime from the date by adding a zero time"""
    return datetime.combine(date, datetime.min.time())


def daycount(start_date, end_date):
    """Number of days between two dates"""
    return int((end_date - start_date).days) + 1


def daterange(start_date, end_date):
    """Yiels every date between two given dates including start date"""
    for n in range(daycount(start_date, end_date)):
        yield start_date + timedelta(n)


class VoiceActivity(Base):
    """Tracking: Daily voice chat activity
    Each row is one user being online from that point in time
    """

    __tablename__ = "stats_voice_activity"

    datetime = Column(DateTime, primary_key=True, default=datetime.utcnow)
    user_id = Column(Integer, primary_key=True)


class TextActivity(Base):
    """Tracking: Daily chat activity
    Each row is one user being online from that point in time
    """

    __tablename__ = "stats_text_activity"

    datetime = Column(DateTime, primary_key=True, default=datetime.utcnow)
    user_id = Column(Integer, primary_key=True)


class DailyResume(Base):
    """Historical: computed from tracking tables"""

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

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot goes online"""
        # Delete all tracking left
        self.session.query(TextActivity).delete()
        self.session.query(VoiceActivity).delete()

        self.check_online()

    def clear_member(self, id):
        """In case a user leaves the guild, we remove tracking data for him"""
        self.session.query(TextActivity).filter(
            TextActivity.user_id == id
        ).delete()

        self.session.query(VoiceActivity).filter(
            VoiceActivity.user_id == id
        ).delete()

    def check_online(self):
        """For every online member in text/voice:
        Adds an entry into TRACKING data
        """
        for member in self.bot.get_guild().members:
            if member.bot:
                continue

            if self.bot.is_text_online(member):
                self.track_text_activity(member)

            if self.bot.is_voice_online(member.voice):
                self.track_voice_activity(member)

    def compute_all_uptime(self):
        """Update uptime data for every users"""
        # Text
        for row in self.session.query(TextActivity):
            member = self.bot.get_guild().get_member(row.user_id)

            if member is None:
                self.clear_member(row.user_id)
            else:
                self.compute_member_uptime(TextActivity, member)

        # Voice
        for row in self.session.query(VoiceActivity):
            member = self.bot.get_guild().get_member(row.user_id)

            if member is None:
                self.clear_member(row.user_id)
            else:
                self.compute_member_uptime(VoiceActivity, member)

    def compute_member_uptime(self, model, member):
        """Compute uptime for a particular user"""
        if member.bot:
            return

        tracking = (
            self.session.query(model).filter(model.user_id == member.id).first()
        )

        if not tracking:
            return

        last_online = tracking.datetime
        for current_date in daterange(tracking.datetime.date(), date.today()):
            uptime = 0

            # Get next day at midnight
            next_midgnight = date_to_datetime(current_date) + timedelta(days=1)

            # The day processed is today
            if current_date == date.today():
                uptime = datetime.utcnow() - last_online
            # The day processed is a previous day
            else:
                uptime = next_midgnight - last_online

            last_online = next_midgnight

            # Update daily resume uptime for that day
            historical = self.get_daily_default(member, current_date)

            if model == TextActivity:
                historical.chat_time += uptime.total_seconds()
            else:
                historical.voice_time += uptime.total_seconds()

            self.session.commit()

        # Update row time
        tracking.datetime = datetime.utcnow()

        self.session.commit()

    def track_text_activity(self, member):
        """Record when a user becomes online in text"""
        self.track_activity(TextActivity, member)

    def track_voice_activity(self, member):
        """Record when a user becomes online in voice"""
        self.track_activity(VoiceActivity, member)

    def track_activity(self, model, member):
        """Generic activity tracking update"""
        activity = self.bot.get_or_create(
            self.session, model, user_id=member.id
        )
        activity.datetime = datetime.utcnow()

        self.session.commit()

    def track_clear(self, model, member):
        """Clear tracking about an user (when going offline)"""
        trackings = (
            self.session.query(model).filter(model.user_id == member.id).all()
        )

        for tracking in trackings:
            self.session.delete(tracking)

        self.session.commit()

    def get_daily_default(self, member, date=date.today()):
        """Get the member/day historical record"""
        date = date_to_datetime(date)

        return self.bot.get_or_create(
            self.session, DailyResume, date=date, user_id=member.id
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        When we receive a message
        """
        if message.author.bot:
            return

        row = self.get_daily_default(message.author)
        row.message_count += 1

        self.session.commit()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.bot:
            return

        # Text activity changed
        if self.bot.is_text_online(before) != self.bot.is_text_online(after):
            self.compute_member_uptime(TextActivity, after)

        if self.bot.is_text_online(after):
            self.track_text_activity(after)
        else:
            self.track_clear(TextActivity, after)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        # Voice activity changed
        if self.bot.is_voice_online(before) != self.bot.is_voice_online(after):
            self.compute_member_uptime(VoiceActivity, member)

        if self.bot.is_voice_online(after):
            self.track_voice_activity(member)
        else:
            self.track_clear(VoiceActivity, member)

    def generate_leaderboard(self, query):
        """Given a ordonned query, give a formatted output for a leaderboard"""
        board = ""
        for i in range(3):
            try:
                data = query[i]
                user_name = self.bot.get_guild().get_member(data[0])
                score = data[1]

                if not user_name:
                    user_name = "(leaver)"

                if score == 0:
                    continue

            except Exception:
                continue

            string_format = "{}: {} - *{}*\n"
            # For seconds
            if type(score) is float:
                board += string_format.format(
                    i + 1, self.print_time(self.sec_to_delta(score)), user_name
                )
            else:
                board += string_format.format(i + 1, score, user_name)

        return board

    @commands.command(name="stop")
    async def leaderboard(self, ctx):
        """Provides a leaderboard on various statistics for the server"""
        self.compute_all_uptime()

        # Message sent per day
        sent_count = (
            self.session.query(
                DailyResume.user_id,
                func.sum(DailyResume.message_count).label("sent_count"),
            )
            .group_by(DailyResume.user_id)
            .order_by(func.sum(DailyResume.message_count).desc())
            .limit(3)
        )

        # Total text online per users
        text_online = (
            self.session.query(
                DailyResume.user_id,
                func.sum(DailyResume.chat_time).label("text_online"),
            )
            .group_by(DailyResume.user_id)
            .order_by(func.sum(DailyResume.chat_time).desc())
            .limit(3)
        )

        # Total voice online per users
        voice_online = (
            self.session.query(
                DailyResume.user_id,
                func.sum(DailyResume.voice_time).label("voice_online"),
            )
            .group_by(DailyResume.user_id)
            .order_by(func.sum(DailyResume.voice_time).desc())
            .limit(3)
        )

        top_messages = self.generate_leaderboard(sent_count)
        top_uptime = self.generate_leaderboard(text_online)
        top_voice = self.generate_leaderboard(voice_online)

        await ctx.send(
            ">>> __Leaderboard__\n"
            "**Messages sent:**\n{}"
            "**Uptime:**\n{}"
            "**Voice chat:**\n{}".format(
                top_messages,
                top_uptime,
                top_voice,
            )
        )

    @commands.command(name="suser")
    async def user_statistics(self, ctx, user_name):
        """Provides statistics about a particular user"""
        member = self.bot.get_guild().get_member_named(user_name)

        if not member:
            await ctx.send(
                "Cet utilisateur n'a pas pu être trouvé. "
                "Respectez le format suivant: "
                "username#discriminator (test#0123)"
            )
            return

        if member.bot:
            await ctx.send("Why do you care about bots ?")
            return

        self.compute_all_uptime()

        today = date_to_datetime(date.today())
        month = today.replace(day=1)

        message_sent = self.query_message_per_day().filter(
            DailyResume.user_id == member.id
        )

        # Total messages
        sum_message_sent = self.session.query(
            func.sum(message_sent.subquery().c.count)
        ).scalar()

        if sum_message_sent is None:
            sum_message_sent = 0

        # Avearage message sent
        try:
            avg_message_sent = sum_message_sent / daycount(
                message_sent.first()[0], today
            )
        except TypeError:
            avg_message_sent = 0

        # Avearage message sent this month
        try:
            sum_message_sent_month = self.session.query(
                func.sum(
                    message_sent.filter(DailyResume.date >= month)
                    .subquery()
                    .c.count
                )
            ).scalar()
            avg_message_sent_month = sum_message_sent_month / daycount(
                month, today
            )
        except TypeError:
            avg_message_sent_month = 0

        # Sum of time spent online in voice today
        sum_voice_online = (
            self.session.query(func.sum(DailyResume.voice_time))
            .filter(
                and_(
                    DailyResume.user_id == member.id, DailyResume.date >= today
                )
            )
            .scalar()
        )

        # Sum of time spent online in voice all time
        sum_voice_online_total = (
            self.session.query(func.sum(DailyResume.voice_time))
            .filter(DailyResume.user_id == member.id)
            .scalar()
        )

        await ctx.send(
            ">>> __Stats for user {}__\n"
            "**Messages sent total:** {}\n"
            "**Average messages per day:** {:.2f}\n"
            "**Average messages this month:** {:.2f}\n"
            "\n"
            "**Total time in voice today:** {}\n"
            "**Total time in voice:** {}".format(
                member.name,
                sum_message_sent,
                avg_message_sent,
                avg_message_sent_month,

                self.bot.print_time(self.bot.sec_to_delta(sum_voice_online)),
                self.bot.print_time(self.bot.sec_to_delta(sum_voice_online_total)),
        ))

    @commands.command(name="stats")
    async def statistics(self, ctx):
        """Provides general statistics about server and bot usage"""
        self.compute_all_uptime()

        today = date_to_datetime(date.today())
        month = today.replace(day=1)

        online_users = self.query_online_per_day()
        message_sent = self.query_message_per_day()

        # Online users today
        online_users_today = online_users.filter(
            DailyResume.date == today
        ).one()[1]

        # Messages sent today
        message_sent_today = message_sent.filter(
            DailyResume.date == today
        ).one()[1]

        # Avearage daily online
        sum_online_users = self.session.query(
            func.sum(online_users.subquery().c.count)
        ).scalar()
        avg_online_users = sum_online_users / daycount(
            online_users.first()[0], today
        )

        # Avearage message sent
        sum_message_sent = self.session.query(
            func.sum(message_sent.subquery().c.count)
        ).scalar()
        avg_message_sent = sum_message_sent / daycount(
            message_sent.first()[0], today
        )

        # Avearage message sent this month
        sum_message_sent_month = self.session.query(
            func.sum(
                message_sent.filter(DailyResume.date >= month)
                .subquery()
                .c.count
            )
        ).scalar()
        avg_message_sent_month = sum_message_sent_month / daycount(month, today)

        # Total text online per users
        text_online = self.session.query(
            DailyResume.user_id,
            func.sum(DailyResume.chat_time).label("text_online"),
        ).group_by(DailyResume.user_id)

        # Total voice online per users
        voice_online = self.session.query(
            DailyResume.user_id,
            func.sum(DailyResume.voice_time).label("voice_online"),
        ).group_by(DailyResume.user_id)

        # Average time text online
        avg_text_online = self.session.query(
            func.avg(text_online.subquery().c.text_online)
        ).scalar()

        avg_text_online_month = self.session.query(
            func.avg(
                text_online.filter(DailyResume.date >= month)
                .subquery()
                .c.text_online
            )
        ).scalar()

        # Average time voice online
        avg_voice_online = self.session.query(
            func.avg(voice_online.subquery().c.voice_online)
        ).scalar()

        avg_voice_online_month = self.session.query(
            func.avg(
                voice_online.filter(DailyResume.date >= month)
                .subquery()
                .c.voice_online
            )
        ).scalar()

        z14_uptime = datetime.utcnow() - self.started_at

        # Sum of time spent online in voice by all users today
        sum_voice_online = (
            self.session.query(func.sum(DailyResume.voice_time))
            .filter(DailyResume.date >= today)
            .scalar()
        )

        # Sum of time spent online in voice by all users all time
        sum_voice_online_total = self.session.query(
            func.sum(DailyResume.voice_time)
        ).scalar()

        await ctx.send(
            ">>> __Statistics__\n"
            "**z14 uptime:** {}\n"
            "\n"
            "**Total users:** {}\n"
            "**Users online today:** {}\n"
            "**Average users online per day:** {:.2f}\n"
            "\n"
            "**Messages sent today:** {}\n"
            "**Average messages per day:** {:.2f}\n"
            "**Average messages this month:** {:.2f}\n"
            "\n"
            "**Total time in voice today:** {}\n"
            "**Total time in voice:** {}\n"
            "\n"
            "**Average time connected in text/day:** {}\n"
            "**Average time connected in voice/day:** {}\n"
            "**Average time connected in text/month:** {}\n"
            "**Average time connected in voice/month:** {}".format(
                self.bot.print_time(z14_uptime),

                len(ctx.guild.members),
                online_users_today,
                avg_online_users,
                message_sent_today,
                avg_message_sent,
                avg_message_sent_month,

                self.bot.print_time(self.bot.sec_to_delta(sum_voice_online)),
                self.bot.print_time(self.bot.sec_to_delta(sum_voice_online_total)),

                self.bot.print_time(self.bot.sec_to_delta(avg_text_online)),
                self.bot.print_time(self.bot.sec_to_delta(avg_voice_online)),
                self.bot.print_time(self.bot.sec_to_delta(avg_text_online_month)),
                self.bot.print_time(self.bot.sec_to_delta(avg_voice_online_month)),
        ))

    @user_statistics.error
    async def error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "The following argument is missing: {}".format(error.param)
            )

        else:
            print(
                "Encountered unexpected error: {} {}".format(error, type(error))
            )

    def query_message_per_day(self):
        """Gives a query with number of message sent by day"""
        return (
            self.session.query(
                DailyResume.date,
                func.sum(DailyResume.message_count).label("count"),
            )
            .group_by(DailyResume.date)
            .order_by(DailyResume.date.asc())
        )

    def query_online_per_day(self):
        """Gives a query with number of users online per day"""
        return (
            self.session.query(
                DailyResume.date, func.count(DailyResume.user_id).label("count")
            )
            .filter(DailyResume.chat_time > 0)
            .group_by(DailyResume.date)
            .order_by(DailyResume.date.asc())
        )


def setup(bot):
    bot.add_cog(Statistics(bot))
