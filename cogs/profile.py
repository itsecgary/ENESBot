import discord
from discord.ext import commands, tasks
import string
import json
import sys
import help_info
import traceback
sys.path.append("..")
from config_vars import *

################################ DATA STRUCTURES ###############################

#################################### CLASSES ###################################
class Profile(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def profile(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.send("Invalid command. Run `>help profile` for information on **profile** commands.")

    @profile.command()
    async def me(self, ctx, user=None):
        if user is None:
            await ctx.channel.send("You must choose a profile to see")
        if user == "me":
            await ctx.channel.send("The **me** command is currently in progress")
        else:
            await ctx.channel.send("The **me** command is currently in progress")

#################################### SETUP #####################################
def setup(bot):
    bot.add_cog(Profile(bot))
