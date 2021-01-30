import os
import datetime
import asyncio

from discord.ext import commands


class KickMalabar(commands.Cog):
    """ Command that will mute Malabar
    """
    def __init__(self, bot):
        self.bot = bot
        self.history = []
        self.mute_time = int(os.getenv("MALABAR_MUTE_TIME"))
        self.history_max_size = int(os.getenv("MALABAR_HISTORY_MAX_SIZE"))
        self.history_max_time = datetime.timedelta(
            hours=int(os.getenv("MALABAR_HISTORY_MAX_TIME")))

        self.is_currently_muted = False


    def test(self):
        assert not os.getenv("MALABAR") is None, "MALABAR is not defined"
        assert not os.getenv("MALABAR_HISTORY_MAX_SIZE") is None, \
            "MALABAR_HISTORY_MAX_SIZE is not defined"
        assert not os.getenv("MALABAR_HISTORY_MAX_TIME") is None, \
            "MALABAR_HISTORY_MAX_TIME is not defined"
        assert not os.getenv("MALABAR_MUTE_TIME") is None, \
            "MALABAR_MUTE_TIME is not defined"

        try:
            mute = int(os.getenv("MALABAR_MUTE_TIME"))
            time = int(os.getenv("MALABAR_HISTORY_MAX_TIME"))
            size = int(os.getenv("MALABAR_HISTORY_MAX_SIZE"))
        except Exception as e:
            self.fail("One of the variable is not a proper integer")


    def update_history(self):
        """ Remove entries in history older than the threshold
        """
        old_history = self.history.copy()

        self.history.clear()

        for when in old_history:
            if when - datetime.datetime.utcnow() > self.history_max_time:
                continue

            self.history.append(when)


    def can_call(self):
        """ Return True if we can mute Malabar
        - We can call if history size is smaller than
        """
        return len(self.history) < self.history_max_size


    async def update_mute(self):
        if self.malabar.voice:
            await self.malabar.edit(mute=self.is_currently_muted)


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member is self.malabar:
            return

        # Connect
        if before.channel is None and not after.channel is None:
            await self.update_mute()


    @commands.Cog.listener()
    async def on_ready(self):
        malabar_name = os.getenv("MALABAR", default="")
        self.malabar = self.bot.get_guild().get_member_named(malabar_name)


    @commands.command(name="km")
    async def kick_malabar(self, ctx):
        """ Mute Malabar for some time
        """
        self.update_history()

        if not self.can_call():
            await ctx.send("Slow down there...")

            print("""km threshold of {} times during the last {} \
                hours reached""".format(
                    len(self.history), os.getenv("MALABAR_HISTORY_MAX_TIME")
                )
            )

        elif not self.malabar:
            await ctx.send("Il est parti du serveur :'(")

            print("Trying to mute {} while he's not there...".format(
                os.getenv("MALABAR")
            ))

        elif self.is_currently_muted:
            await ctx.send("He is already muted... Slow down...")

            print("Trying to mute while already muted...")

        else:
            self.is_currently_muted = True
            await self.update_mute()

            await ctx.send("{} TAGUEULE".format(self.malabar.mention))

            self.history.append(datetime.datetime.utcnow())
            print("km invoked {} times during the last {} hours".format(
                len(self.history), os.getenv("MALABAR_HISTORY_MAX_TIME")
            ))

            await asyncio.sleep(self.mute_time)

            self.is_currently_muted = False
            await self.update_mute()

            print("{} is now free to speak".format(
                os.getenv("MALABAR")
            ))
