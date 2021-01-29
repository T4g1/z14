import os
import datetime

from discord.ext import commands


class ScoreRecord():
    """
    Represent a scoring command sent
    """
    def __init__(self, when, score):
        self.when = when
        self.score = score


class ScoreTracker(commands.Cog):
    """
    Track T4g1 scores on jokes, provide its current average score as well as
    useful statistics
    """
    def __init__(self, bot):
        self.bot = bot
        self.tracker_user = None
        self.history = []
        self.fix_time = datetime.timedelta(
            minutes=int(os.getenv("SCORE_TRACKER_FIX_TIME")))


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
        self.history.append(ScoreRecord(datetime.datetime.utcnow(), score))

        try:
            score = await self.sanitize_score(ctx, score)
        except ValueError:
            return

        if score > 0:
            await ctx.send("GG {}!".format(self.tracker_target.mention))
        elif score == 0:
            await ctx.send("Coucou {}!".format(self.tracker_target.mention))
        else:
            await ctx.send("It's bad {}!".format(self.tracker_target.mention))


    @commands.command()
    async def fix(self, ctx, score):
        """ ..fix x: Used to fix the latest score entered
        Available during SCORE_TRACKER_CORRECTION_TIME minutes
        """
        if len(self.history) <= 0:
            await ctx.send("I have no score to fix!")
            return

        if datetime.datetime.utcnow() - self.history[-1].when > self.fix_time:
            await ctx.send("It's too late to go back now, " \
                "you will have to live with that mistake forever")
            return

        try:
            score = await self.sanitize_score(ctx, score)
        except ValueError:
            return

        previous = self.history[-1].score
        self.history[-1].score = score

        await ctx.send("Previous score changed from {} to {}".format(
            previous, score
        ))
