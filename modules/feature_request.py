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
    async def feature_request(self, ctx, *args):
        """ Send a PM to the user telling them its the worst idea ever
        Usage: .fr "[titre]" "[description]"
        """
        if len(args) != 2:
            await ctx.send("usage: .fr 'title' 'description'")

            await ctx.author.send("Abruti")
            return

        await ctx.send(
            "Votre suggestion pour la feature suivante a bien " \
            "été prise en compte:\n{}\n{}".format(args[0], args[1]))

        await ctx.author.send("Eh bé tu peux te la mettre ou je pense ta propal")
