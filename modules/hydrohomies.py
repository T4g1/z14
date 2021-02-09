import asyncio
import os
import aiohttp
import discord
import random

from discord.ext import commands, tasks

# These two variables determine how the posts embed will cycle
# If max size is too high or limit too low, nothing will get embedded
HISTORY_MAX_SIZE = 10
REDDIT_LIMIT = 50

SENTENCES = [
    "Don't forget to drink water!",
    "Please drink some water",
    "Water is life, drink it!",
    "A bottle of water a day keeps the doctor at bay",
    "When is the last time you drank water ?"
]


class HydroHomies(commands.Cog):
    """
    Reminds everyone to drink water at regular interval in a specific channel
    """
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.lock = asyncio.Lock()

        self.embed_history = []
        self.subreddit = ""


    def test(self):
        assert not os.getenv("HYDRO_CHANNEL") is None, \
            "HYDRO_CHANNEL is not defined"
        assert not os.getenv("HYDRO_SUB") is None, \
            "HYDRO_SUB is not defined"

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

        self.subreddit = os.getenv("HYDRO_SUB")

        timer = int(os.getenv("HYDRO_TIMER", default=7200))
        self.hydrohomies. change_interval(seconds=timer)
        self.hydrohomies.start()


    async def get_embedable(self):
        """ Query reddit's API to get an embedable
        """
        if self.bot.reddit is None:
            return (None, None)

        # Prune history
        self.embed_history = self.embed_history[-HISTORY_MAX_SIZE:]

        title = None
        embedable = None

        subreddit = await self.bot.reddit.subreddit(self.subreddit)
        async for submission in subreddit.top(limit=REDDIT_LIMIT):
            # Text submission
            if submission.is_self:
                continue

            # Not an image
            if (not submission.is_reddit_media_domain or
                submission.domain != "i.redd.it"):
                continue

            # Already used
            if submission.url in self.embed_history:
                continue

            title = "**Brought to you by:** {}".format(submission.title)
            embedable = submission.url

        self.embed_history.append(embedable)

        return (title, embedable)


    def get_reminder(self):
        """ Give a text saying when the next reminder is
        """
        return "Next hydroreminder: {}".format(
            self.hydrohomies.next_iteration.strftime(
                "%d/%m/%Y %H:%M:%S UTC"
            )
        )


    @tasks.loop(seconds=10)
    async def hydrohomies(self):
        async with self.lock:
            embed = None

            title, image_url = await self.get_embedable()
            if image_url:
                embed = discord.Embed()
                embed.set_image(url=image_url)
            else:
                title = self.get_reminder()

            await self.channel.send(
                "{}\n{}".format(
                    random.choice(SENTENCES),
                    title
                ), embed=embed)

            print(self.get_reminder())



def setup(bot):
    bot.add_cog(HydroHomies(bot))

