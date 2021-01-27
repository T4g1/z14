import argparse
import discord
import os

from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()

bot = commands.Bot(command_prefix='.')


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.command(name="km")
async def kick_malabar(ctx):
    await ctx.send("MALABAR TAGEULE")


bot.run(os.getenv('TOKEN'))
