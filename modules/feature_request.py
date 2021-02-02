from discord.ext import commands


class FeatureRequest(commands.Cog):
    """
    Will show Paglops what she can do with her shitty feature requests
    """
    def __init__(self, bot):
        self.bot = bot


    def test(self):
        pass


    @commands.command(name="fr")
    async def feature_request(self, ctx, title, description):
        """ [titre] [description]: Send a PM to the user telling them its the worst idea ever
        Usage: .fr "[titre]" "[description]"
        """
        await ctx.send(
            "Votre suggestion pour la feature suivante a bien " \
            "été prise en compte:\n{}\n{}".format(title, description))

        await ctx.author.send("Eh bé tu peux te la mettre ou je pense ta propal")


    @feature_request.error
    async def error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("usage: .fr 'title' 'description'")
            await ctx.author.send("Abruti")

        else:
            print("Encountered unexpected error: {} {}".format(error, type(error)))


def setup(bot):
    bot.add_cog(FeatureRequest(bot))


def teardown(bot):
    print('Reloading {}'.format('modules.feature_request'))
