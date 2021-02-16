import os
import datetime
import asyncio


from discord.ext import commands


class KickMalabar(commands.Cog):
    """
    Command that will mute Malabar
    """

    def __init__(self, bot):
        self.bot = bot
        self.history = []
        self.mute_time = int(os.getenv("MALABAR_MUTE_TIME"))
        self.history_max_size = int(os.getenv("MALABAR_HISTORY_MAX_SIZE"))
        self.history_max_time = datetime.timedelta(
            hours=int(os.getenv("MALABAR_HISTORY_MAX_TIME"))
        )

        self.is_currently_muted = False
        self.malabar = None

    def test(self):
        assert not os.getenv("MALABAR") is None, "MALABAR is not defined"
        assert (
            not os.getenv("MALABAR_HISTORY_MAX_SIZE") is None
        ), "MALABAR_HISTORY_MAX_SIZE is not defined"
        assert (
            not os.getenv("MALABAR_HISTORY_MAX_TIME") is None
        ), "MALABAR_HISTORY_MAX_TIME is not defined"
        assert (
            not os.getenv("MALABAR_MUTE_TIME") is None
        ), "MALABAR_MUTE_TIME is not defined"

        try:
            _ = int(os.getenv("MALABAR_MUTE_TIME"))
            _ = int(os.getenv("MALABAR_HISTORY_MAX_TIME"))
            _ = int(os.getenv("MALABAR_HISTORY_MAX_SIZE"))
        except Exception:
            self.fail("One of the variable is not a proper integer")

    def update_history(self):
        """Remove entries in history older than the threshold"""
        old_history = self.history.copy()

        self.history.clear()

        for when in old_history:
            if datetime.datetime.utcnow() - when > self.history_max_time:
                continue

            self.history.append(when)

    def can_call(self):
        """Return True if we can mute Malabar
        - We can call if history size is smaller than
        """
        return len(self.history) < self.history_max_size

    async def update_mute(self):
        if self.malabar.voice:
            await self.malabar.edit(mute=self.is_currently_muted)

    async def malabar_exist(ctx):
        """Checks that Malabar exists on the guild"""
        return ctx.cog.malabar is not None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member is not self.malabar:
            return

        # Connect
        if before.channel is None and after.channel is not None:
            await self.update_mute()

    @commands.Cog.listener()
    async def on_ready(self):
        malabar_name = os.getenv("MALABAR", default="")
        self.malabar = self.bot.get_guild().get_member_named(malabar_name)

    @commands.command(name="km")
    @commands.check(malabar_exist)
    async def kick_malabar(self, ctx):
        """Mute Malabar for some time"""
        self.update_history()

        if not self.can_call():
            await ctx.send("Slow down there...")

            print(
                """km threshold of {} times during the last {} \
                hours reached""".format(
                    len(self.history), os.getenv("MALABAR_HISTORY_MAX_TIME")
                )
            )

        elif self.is_currently_muted:
            await ctx.send("He is already muted... Slow down...")

            print("Trying to mute while already muted...")

        else:
            self.is_currently_muted = True
            await self.update_mute()

            await ctx.send("{} TAGUEULE".format(self.malabar.mention))

            self.history.append(datetime.datetime.utcnow())
            print(
                "km invoked {} times during the last {} hours".format(
                    len(self.history), os.getenv("MALABAR_HISTORY_MAX_TIME")
                )
            )

            await asyncio.sleep(self.mute_time)

            self.is_currently_muted = False
            await self.update_mute()

            print("{} is now free to speak".format(os.getenv("MALABAR")))

    @kick_malabar.error
    async def error_handler(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("I can't kick him if he's not there...")

        else:
            print(
                "Encountered unexpected error: {} {}".format(error, type(error))
            )


def setup(bot):
    bot.add_cog(KickMalabar(bot))
