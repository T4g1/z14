import asyncio
import os

from discord.ext import commands, tasks


class HydroHomies(commands.Cog):
    """
    Reminds everyone to drink water at regular interval in a specific channel
    """
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.lock = asyncio.Lock()


    def test(self):
        assert not os.getenv("HYDRO_CHANNEL") is None, \
            "HYDRO_CHANNEL is not defined"

        try:
            timer = int(os.getenv("HYDRO_TIMER", default=7200))
        except:
            self.fail("HYDRO_TIMER must be an integer")

        try:
            message_id = int(os.getenv("HYDRO_CHANNEL", default="0"))
            assert self.bot.get_guild().get_channel(channel_id) is None, \
                "Given HYDRO_CHANNEL does not exists in this guild"
        except Exception as e:
            self.fail("HYDRO_CHANNEL must be an integer is not an integer")


    @commands.Cog.listener()
    async def on_ready(self):
        channel_id = int(os.getenv("HYDRO_CHANNEL", default="0"))
        self.channel = self.bot.get_guild().get_channel(channel_id)

        timer = int(os.getenv("HYDRO_TIMER", default=7200))
        self.hydrohomies. change_interval(seconds=timer)
        self.hydrohomies.start()


    @tasks.loop(seconds=10)
    async def hydrohomies(self):
        async with self.lock:
            await self.channel.send("Don't forget to drink water!\n" \
                "Next reminder: {}".format(
                    self.hydrohomies.next_iteration.strftime(
                        "%d/%m/%Y %H:%M:%S UTC")
            ))



def setup(bot):
    bot.add_cog(HydroHomies(bot))

