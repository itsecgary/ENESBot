import discord
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import *
from discord.ext import commands, tasks
from itertools import cycle
from config_vars import *
import help_info
import pytz

################################ DATA STRUCTURES ###############################
bot = commands.Bot(command_prefix = '>')
bot.remove_command('help')
extensions = []

#################################### EVENTS ####################################
@bot.event # Show banner and add members to respective guilds in db
async def on_ready():
    print("\n|--------------------|")
    print(f"|  {bot.user.name} - Online   |")
    print(f"|  discord.py {discord.__version__}  |")
    print("|--------------------|")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=">help"))

    # Create current member info
    for guild in bot.guilds:
        break
        print("\n----------------------- {} -----------------------".format(guild.name))
        member_cnt = 0
        for member in guild.members:
            add_member(member, guild)
            if not member.bot: member_cnt += 1

        info = {
            "name": str(guild.name), "num members": member_cnt, "ranking": {}
        }

        infodb['server_info'].update_one({"name": str(guild.name)}, {"$set": info}, upsert=True)
        print("------------------------------------------------{}".format("-"*len(guild.name)))

@bot.event # Displays error messages
async def on_command_error(ctx, error):
    msg = ""
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        msg += "Missing a required argument.  Do >help\n"
    if isinstance(error, commands.MissingPermissions):
        msg += "You do not have the appropriate permissions to run this command.\n"
    if isinstance(error, commands.BotMissingPermissions):
        msg += "I don't have sufficient permissions!\n"
    if msg == "":
        if not isinstance(error, commands.CheckFailure):
            msg += "Something went wrong.\n"
            print("error not caught")
            print(error)
            await ctx.send(msg)
    else:
        await ctx.send(msg)

@bot.event # Adds new member to data structures
async def on_member_join(member):
    print(f'{member} has joined the server')
    for guild in bot.guilds:
        if member in guild.members:
            cnt = add_member(member, guild)
            if cnt == 1:
                server = infodb['server_info'].find_one({'name': str(guild.name)})
                server.update({"num_members": info["num members"] + 1})
            return

@bot.event # Removes existing member from data structures
async def on_member_remove(member):
    print(f'{member} has left the server')
    for guild in bot.guilds:
        if member in guild.members:
            infodb['members'].remove({"name": str(member)})
            return

@bot.event
async def on_member_update(before, after):
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        if new_role.name in ('Level 1  Mastermind', 'Level 2 Mastermind', 'Level 1 Technomancer', 'Level 2 Technomancer'):
            fmt = "{0.mention} has reached `{1}`! :confetti_ball:"
            channel = bot.get_channel(755199728664444989)
            await channel.send(fmt.format(after, new_role.name))
            print(fmt.format(after, new_role.name))
        print("{}'s role received the {} role".format(after.name, new_role.name))
    elif len(after.roles) < len(before.roles):
        lost_role = next(role for role in before.roles if role not in after.roles)
        print("{}'s role lost the {} role".format(after.name, lost_role.name))

@bot.event
async def on_message(ctx):
    if 'enesbot' in ctx.content.lower():
        await ctx.channel.send("who said my name")
    elif 'bad bot' in ctx.content.lower():
        await ctx.channel.send("no u")
    elif 'good bot' in ctx.content.lower():
        await ctx.channel.send("thank")
    elif 'LTF' in ctx.content:
        await ctx.channel.send("LTF > UTF")
    #if str(ctx.channel.type) == "private" or str(ctx.guild.id) == '734854267847966720' or ctx.channel.name == 'ctf-bot-dev':
    await bot.process_commands(ctx)

################################ OTHER FUNCTIONS ###############################
@bot.command()
async def help(ctx, page=None):
    emb = discord.Embed(description=help_info.help_page, colour=discord.Colour.orange())
    emb.set_author(name='ENESBot Help')
    await ctx.channel.send(embed=emb)

@bot.command()
async def available(ctx, option):
    if option not in ['IP', 'OOO', 'OL']:
        await ctx.channel.send("Invalid argument")
        return

    # Fixing timezone to Eastern only
    oldtime = datetime.now()
    eastern = pytz.timezone("US/Eastern")
    time = oldtime.astimezone(eastern)

    # Connecting to office hour spreadsheet using Google Sheets API
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('enesbot-2dfbe5f92e4b.json', scope)
    client = gspread.authorize(creds)
    ss = client.open("100F21 Office Hours")
    sheet = ss.get_worksheet(0)

    print(sheet.col_values(11)[4:])
    print(sheet.col_values(12)[4:])
    print(sheet.col_values(13)[4:])
    print(sheet.col_values(14)[4:])
    print(sheet.col_values(15)[4:])

    hour = time.hour
    index = hour - 9
    day = time.weekday()
    day_index = 0

    if datetime.now().timetuple().tm_yday < 249:
        day_index = ((day)*5) + 1
    else:
        # get the correct index for day in spreadsheet
        if day == 6:
            day_index = 1
        else:
            day_index = ((day+1)*5) + 1

    print(f'hour = {hour}')
    print(f'day = {day}')
    print(day_index)

    # Getting names and zoom links
    loop = 1
    if option == 'OOO':
        day_index += 4
    elif option == 'IP':
        day_index += 3
    else:
        day_index += 1
        loop = 2

    # Composing message with TA names and zoom links for those available
    if option == "OL":
        if hour < 19 and day != 5 and hour != 9:
            message = "**JMP1201 (small lab)**: "
            if day == 0 or day == 2 or hour < 16:
                print(sheet.col_values(day_index)[4:][1])
                message += sheet.col_values(day_index)[4:][1]
            else:
                avail = ''
                if len(sheet.col_values(day_index)[4:]) >= index+1:
                    avail = sheet.col_values(day_index)[4:][index]
                    message += avail
                if len(avail) == 0:
                    message += 'none :('

            message += "\n**JMP1120 (big lab)**: "
            print(sheet.col_values(day_index+1)[4:][1])
            if hour < 16:
                print(sheet.col_values(day_index+1)[4:][1])
                message += sheet.col_values(day_index+1)[4:][1]
            else:
                avail = ''
                if len(sheet.col_values(day_index+1)[4:]) >= index+1:
                    avail = sheet.col_values(day_index+1)[4:][index]
                    message += avail
                if len(avail) == 0:
                    message += 'none :('

        elif hour < 22 and day != 5: # if not saturday and is before 10pm
            message = "**JMP1201 (small lab)**: "
            print(sheet.col_values(day_index)[4:])
            if len(sheet.col_values(day_index)[4:]) >= index+1:
                avail = sheet.col_values(day_index)[4:][index]
                message += avail
            if len(avail) == 0:
                message += 'none :('

            message += "\n**JMP1120 (big lab)**: "
            print(sheet.col_values(day_index+1)[4:])
            if len(sheet.col_values(day_index+1)[4:]) >= index+1:
                avail = sheet.col_values(day_index+1)[4:][index]
                message += avail
            if len(avail) == 0:
                message += 'none :('
        else:
            message = "No one be in the labs :("
    else:
        if hour < 22 and day != 5: # if not saturday and is before 10pm
            link = ""
            message = "**Available Faculty:** "
            if len(sheet.col_values(day_index)[4:]) >= index+1:
                avail = sheet.col_values(day_index)[4:][index]
                message += str(avail)
            if len(avail) == 0:
                message += "none :("
        else:
            message = "**Available Faculty:** None :("

    print(message)
    await ctx.channel.send(message)

@bot.command()
async def hours(ctx, ta_prof=None):
    if ta_prof is None:
        await ctx.channel.send("Invalid number of arguments")
    else:
        print(ta_prof)
        await ctx.channel.send("The **hours** command is currently in progress")

@bot.command()
async def officehours(ctx, cclass):
    classes = {"enes100": "<https://docs.google.com/spreadsheets/d/1Y6pVgPkDEDIOop94Z1x8-HsUthPRjajxAIBWD-TyK4E>",
               "enes102": "<https://docs.google.com/spreadsheets/u/1/d/1wBB8DZxcPUTl5dWyulhcDJzZ6Z7dNyI4C0kNqSBvnL4/preview>"}

    if cclass.lower() == "enes100":
        await ctx.channel.send(classes[cclass.lower()])
    elif cclass.lower() == "enes102":
        await ctx.channel.send(classes[cclass.lower()])
    else:
        await ctx.channel.send("Class not found")

##################################### MAIN #####################################
if __name__ == '__main__': # Loads cog extentions and starts up the bot
    print("\n|-----------------------|\n| Loaded Cogs:          |")
    for extension in extensions:
        bot.load_extension('cogs.' + extension)
        print("|   - {}   {}|".format(extension.upper(), " "*(15-len(extension))))
    print("|-----------------------|\n")
    bot.run(discord_token)
