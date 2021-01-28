import argparse
import discord
import os

from dotenv import load_dotenv
from discord.ext import commands


load_dotenv()

intents = discord.Intents.default()
intents.reactions = True
intents.members = True

roles_mapping = {}

bot = commands.Bot(command_prefix='.', intents=intents)


def get_guild():
    """Return the main guild
    """
    return bot.guilds[0]


def get_role_message_id():
    """Gives the ID of the message used to allow users to select their roles
    """
    try:
        message_id = os.getenv("ROLE_MESSAGE_ID", default="0")
        return int(message_id)
    except Exception as e:
        print("Error while trying to read ROLE_MESSAGE_ID, \
            make sure it's defined and it is an integer")

    return 0


def extract_roles_mapping(guild):
    """ Extract mapping of emoji to role to assign roles to users
    that add the emoji to the message with ID ROLE_MESSAGE_ID
    """
    raw_mapping = os.getenv("ROLE_EMOJIS", default="")

    bot.roles_mapping = {}

    try:
        raw_mappings = raw_mapping.split(";")

        for raw_mapping in raw_mappings:
            if raw_mapping == "":
                continue

            emoji, role_name = raw_mapping.split(",")
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                print("Role {} not found on that server, ignored".format(
                    role_name
                ))
                continue

            bot.roles_mapping[emoji] = role
    except Exception as e:
        print("ROLE_EMOJIS is badly formatted: \
            :[EMOJI 1]:,[ROLE 1];:[EMOJI 2]:,[ROLE 2]")
        return

    print("Self role feature has loaded the following roles: ")
    print(bot.roles_mapping)


async def manage_role(payload, remove=False):
    """
    Analyse the payload's emoji to determine which role to add or remove
    """
    member = get_guild().get_member(payload.user_id)

    if not payload.emoji.name in bot.roles_mapping.keys():
        if remove:
            return

        # Remove the emoji
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, member)
        return

    role = bot.roles_mapping[payload.emoji.name]

    if remove:
        await member.remove_roles(role)

        print("Removing role {} from {}".format(
            role.name, member.name
        ))
    else:
        await member.add_roles(role)

        print("Adding role {} to {}".format(
            role.name, member.name
        ))


def self_test():
    assert not os.getenv("TOKEN") is None, \
        "TOKEN not found: Make sur you have a .env at z14 root"

    assert not os.getenv("AUTO_ROLE") is None, "AUTO_ROLE is not defined"
    assert not os.getenv("MALABAR") is None, "MALABAR is not defined"
    assert not os.getenv("ROLE_MESSAGE") is None, "ROLE_MESSAGE is not defined"
    assert not os.getenv("ROLE_EMOJIS") is None, "ROLE_EMOJIS is not defined"


@bot.event
async def on_ready():
    """ Called when z14 is connected and ready to receive events
    """
    self_test()

    if len(bot.guilds) > 1:
        print("Warning: z14 is connected to too many guilds, only the first \
            one will be used")

    extract_roles_mapping(get_guild())

    print("z14 is ready")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != get_role_message_id():
        return

    await manage_role(payload, remove=False)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != get_role_message_id():
        return

    await manage_role(payload, remove=True)


@bot.event
async def on_member_join(member):
    """ Gives new member a pre-defined role
    """
    auto_role = os.getenv("AUTO_ROLE", default="Joueur")

    role = discord.utils.get(member.guild.roles, name=auto_role)
    if role:
        await member.add_roles(role)
    else:
        print("AUTO_ROLE not found! Create a role named {}".format(auto_role))


@bot.command()
async def ping(ctx):
    """ Reply pong to every ping command
    """
    await ctx.send('pong')


@bot.command(name="km")
async def kick_malabar(ctx):
    """ Mute Malabar
    """
    malabar_name = os.getenv("MALABAR", default="")
    if not malabar_name:
        print("You have'nt configured a malabar username")
        return

    malabar = ctx.guild.get_member_named(malabar_name)
    if not malabar:
        print("{} is not on the server...".format(malabar_name))
        return

    await ctx.send("{} TAGUEULE".format(malabar.mention))


bot.run(os.getenv("TOKEN"))
