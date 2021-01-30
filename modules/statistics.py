import pandas as pd
import os
import discord

from discord.ext import commands
from datetime import date


DEFAULT_PATH = "daily_data.dat"

class Statistics(commands.Cog):
    """
    Provide various statistics
    """
    def __init__(self, bot):
        self.bot = bot

        self.today = date.today()
        self.today_online = []

        self.daily_data = pd.DataFrame()
        self.load()


    def test(self):
        assert not os.getenv("STATS_DATA_PATH") is None, \
            "STATS_DATA_PATH is not defined"


    def persist(self):
        """
        Save the following data:
        - today date
        - online_today list
        - today_msg_count
        """
        self.daily_data.to_csv(
            os.getenv("STATS_DATA_PATH", default=DEFAULT_PATH), index=False)


    def load(self):
        """ Load saved data
        """
        try:
            self.daily_data = pd.read_csv(
                os.getenv("STATS_DATA_PATH", default=DEFAULT_PATH),
                 parse_dates=["date"]
             )
        except FileNotFoundError:
            pass

        if len(self.daily_data) == 0:
            self.daily_data = pd.DataFrame.from_dict({
                "date": [],
                "online_count": [],
                "message_count": [],
            })

        self.daily_data = self.daily_data.set_index("date")

        print("Loaded {} daily data".format(len(self.daily_data)))


    @commands.Cog.listener()
    async def on_ready(self):
        self.on_day_changed()


    @commands.command(name="stats")
    async def statistics(self, ctx):
        """
        Provides somewhat useful statistics to users
        """
        await ctx.send("There is {} users on the server!\n" \
            "Users online today: {}\n" \
            "Messages sent today: {}".format(
            len(ctx.guild.members),
            self.daily_data.loc[date.today()]["online_count"],
            self.daily_data.loc[date.today()]["message_count"],
        ))


    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Activity changed
        if before.status != after.status:
            if after.status == discord.Status.online:
                self.on_member_online(after)


    @commands.Cog.listener()
    async def on_message(self, message):
        """
        When we receive a message
        """
        if date.today() != self.today:
            self.on_day_changed()

        self.daily_data.loc[date.today()]["message_count"] += 1


    def on_member_online(self, member):
        """ Record when a user becomes online
        """
        if date.today() != self.today:
            self.on_day_changed()

        if member.id in self.today_online:
            return

        self.today_online.append(member.id)

        self.daily_data.loc[date.today()]["online_count"] += 1


    def on_day_changed(self):
        """
        Detected the day has changed
        """
        self.today = date.today()
        self.today_online = []

        if not date.today() in self.daily_data:
            index = len(self.daily_data)
            data = self.daily_data.to_dict()
            data["online_count"][date.today()] = 0
            data["message_count"][date.today()] = 0

            self.daily_data = pd.DataFrame.from_dict(data)

        self.check_online()


    def check_online(self):
        """
        Update list of members online
        """
        for member in self.bot.get_guild().members:
            if member.status == discord.Status.online:
                self.on_member_online(member)
