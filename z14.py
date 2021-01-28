import discord
import os
import modules

from dotenv import load_dotenv
from discord.ext import commands


class Z14(commands.Bot):
    def get_guild(self):
        """Return the main guild
        """
        return self.guilds[0]


    def run_test(self):
        assert len(self.guilds) == 1,  \
            "Connected to too many guilds, we support only one right now"

        assert not os.getenv("TOKEN") is None, \
            "TOKEN not found: Make sur you have a .env at z14 root"

        assert not os.getenv("AUTO_ROLE") is None, "AUTO_ROLE is not defined"
        assert not os.getenv("MALABAR") is None, "MALABAR is not defined"
        assert not os.getenv("ROLE_MESSAGE_ID") is None, \
            "ROLE_MESSAGE_ID is not defined"
        assert not os.getenv("ROLE_EMOJIS") is None, "ROLE_EMOJIS is not defined"


    async def on_ready(self):
        """ Called when z14 is connected and ready to receive events
        """
        self.run_test()

        print("z14 is ready")


if __name__ == "__main__":
    load_dotenv()

    intents = discord.Intents.default()
    intents.reactions = True
    intents.members = True

    bot = Z14(command_prefix='.', intents=intents)

    bot.add_cog(modules.AutoRole(bot))
    bot.add_cog(modules.SelfRole(bot))
    bot.add_cog(modules.Ping(bot))
    bot.add_cog(modules.KickMalabar(bot))

    bot.run(os.getenv("TOKEN"))
