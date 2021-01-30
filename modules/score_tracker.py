import os
import pandas as pd

from datetime import datetime, timedelta
from discord.ext import commands


DEFAULT_PATH = "score_tracker.dat"


class ScoreTracker(commands.Cog):
    """
    Track T4g1 scores on jokes, provide its current average score as well as
    useful statistics
    """
    def __init__(self, bot):
        self.bot = bot
        self.tracker_user = None
        self.history = pd.DataFrame()
        self.fix_time = timedelta(
            minutes=int(os.getenv("SCORE_TRACKER_FIX_TIME")))

        self.load()


    def test(self):
        assert not os.getenv("SCORE_TRACKER_USER") is None, \
            "SCORE_TRACKER_USER is not defined"
        assert not os.getenv("SCORE_TRACKER_TARGET") is None, \
            "SCORE_TRACKER_TARGET is not defined"
        assert not os.getenv("SCORE_TRACKER_FIX_TIME") is None, \
            "SCORE_TRACKER_FIX_TIME is not defined"

        try:
            time = int(os.getenv("SCORE_TRACKER_FIX_TIME"))
        except Exception as e:
            self.fail("SCORE_TRACKER_FIX_TIME is not a proper integer")


    def add_score(self, score):
        """ Adds the given score into the data
        Expect a sanitized score
        """
        index = len(self.history)
        data = self.history.to_dict()
        data["date"][index] = datetime.utcnow()
        data["score"][index] = score

        print("T4g1 got a new score: {}".format(score))

        self.history = pd.DataFrame.from_dict(data)

        self.persist()


    def remove_last(self):
        self.history = self.history[-1]

        self.persist()

        print("Score tracker entry removed")


    async def sanitize_score(self, ctx, raw_score):
        try:
            score = int(raw_score)

            if score > 10 or score < -10:
                raise ValueError("Value out of range")

            return score
        except ValueError:
            await ctx.send("It's not a valid score!" \
                " Range is [-10, 10], you gave {}".format(raw_score))

            raise ValueError("Bad value given")


    def load(self):
        """ Load persisted data from disk
        """
        try:
            self.history = pd.read_csv(
                os.getenv("SCORE_TRACKER_PATH", default=DEFAULT_PATH),
                 parse_dates=["date"]
             )
        except FileNotFoundError:
            pass

        if len(self.history) == 0:
            self.history = pd.DataFrame.from_dict({
                "date": [],
                "score": []
            })

        self.history.set_index("date")

        print("Loaded {} tracking data".format(len(self.history)))


    def persist(self):
        """ Persist data on disk
        """
        self.history.to_csv(
            os.getenv("SCORE_TRACKER_PATH", default=DEFAULT_PATH), index=False)


    async def average(self, ctx):
        """ Show average of score
        """
        avg = self.history["score"].sum() / len(self.history)

        await ctx.send("Average score: {:.2f}".format(avg))

        print("Giving score tracking average")


    async def stats(self, ctx):
        """ Displays stats
        """
        df = self.history

        first_of_month = datetime.utcnow().date().replace(day=1)
        first_of_month = datetime.combine(first_of_month, datetime.min.time())

        first_of_year = datetime.utcnow().date().replace(month=1, day=1)
        first_of_year = datetime.combine(first_of_year, datetime.min.time())

        this_week = df["date"] >= datetime.utcnow() - timedelta(weeks=1)
        this_month = df["date"] >= first_of_month
        this_year = df["date"] >= first_of_year

        avg_week = df[this_week]["score"].sum() / len(df[this_week])
        avg_month = df[this_month]["score"].sum() / len(df[this_month])
        avg_year = df[this_year]["score"].sum() / len(df[this_year])

        await ctx.send("Average this week: {:.2f} month: {:.2f} year: {:.2f}\n" \
            "This week: max: {}, min: {}\n" \
            "This month: max: {}, min: {}\n" \
            "All time: max: {}, min: {}".format(
            avg_week, avg_month, avg_year,
            df[this_week]["score"].max(), df[this_week]["score"].min(),
            df[this_month]["score"].max(), df[this_month]["score"].min(),
            df["score"].max(), df["score"].min()
        ))

        print("Giving score tracking stats")


    @commands.Cog.listener()
    async def on_ready(self):
        tracker_user_name = os.getenv("SCORE_TRACKER_USER", default="")
        self.tracker_user = self.bot.get_guild().get_member_named(tracker_user_name)

        tracker_target_name = os.getenv("SCORE_TRACKER_TARGET", default="")
        self.tracker_target = self.bot.get_guild().get_member_named(tracker_target_name)

        assert self.tracker_user, \
            "The privilegied user was not found, check configuration"


    @commands.command()
    async def score(self, ctx, score):
        """ .score x: Add score
        score -x: Remove score
        score avg display score average
        score stats show statistics
        """
        if score == "avg":
            return await self.average(ctx)
        elif score == "stats":
            return await self.stats(ctx)

        if ctx.author != self.tracker_user:
            return await ctx.send("Only {} can use this command!".format(
                self.tracker_user.mention))

        try:
            score = await self.sanitize_score(ctx, score)
        except ValueError:
            return

        self.add_score(score)

        if score > 0:
            await ctx.send("GG {}!".format(self.tracker_target.mention))
        elif score == 0:
            await ctx.send("Coucou {}!".format(self.tracker_target.mention))
        else:
            await ctx.send("It's bad {}!".format(self.tracker_target.mention))


    @commands.command()
    async def fix(self, ctx, score):
        """ fix x: Used to fix the latest score entered
        Available during SCORE_TRACKER_CORRECTION_TIME minutes
        """
        if ctx.author != self.tracker_user:
            return await ctx.send("Only {} can use this command!".format(
                self.tracker_user.mention))

        if len(self.history) <= 0:
            await ctx.send("I have no score to fix!")
            return

        if datetime.utcnow() - self.history.loc[-1]["date"] > self.fix_time:
            await ctx.send("It's too late to go back now, " \
                "you will have to live with that mistake forever")
            return

        try:
            score = await self.sanitize_score(ctx, score)
        except ValueError:
            return

        if self.history.loc[-1].score == score:
            self.remove_last()

            await ctx.send(
                "Previous score removed! Score was: {}".format(score))
        else:
            await ctx.send("Score does not match! Score was: {}".format(
                self.history.loc[-1].score))
