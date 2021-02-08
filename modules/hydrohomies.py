import asyncio
import os

import aiohttp
import discord
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
            channel_id = int(os.getenv("HYDRO_CHANNEL", default="0"))
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

    async def get_latest_img_from_api(self):
        session = aiohttp.ClientSession()
        q = await session.get("https://www.reddit.com/r/HydroHomies/new/.json?count=5")
        r = await q.json()
        await session.close()
        url_img = None
        i = 0
        while url_img is None and i < 5:
            data = r['data']['children'][i]['data']
            if 'url_overridden_by_dest' in data:
                url_img = data['url_overridden_by_dest']
            else:
                i += 1
        return url_img


    @tasks.loop(seconds=10)
    async def hydrohomies(self):
        async with self.lock:
            embed = discord.Embed()
            url_img = await self.get_latest_img_from_api()
            if not url_img:
                embed = None
            else:
                embed.set_image(url=url_img)
            await self.channel.send("Don't forget to drink water!\n" \
                "Next reminder: {}".format(
                    self.hydrohomies.next_iteration.strftime(
                        "%d/%m/%Y %H:%M:%S UTC")
            ), embed=embed)



def setup(bot):
    bot.add_cog(HydroHomies(bot))

