import discord
from discord.ext import commands
import mysql.connector
import random

client = commands.Bot(command_prefix = '!')
queue = []

# Handle DataBase
# create database users_db
users_db = mysql.connector.connect(
      host="localhost",
      user="truueh",
      passwd="truueh2001",
      database="users_db"
    )

cursor = users_db.cursor()

#cursor.execute("TRUNCATE TABLE Users") # clear table users

#cursor.execute("CREATE TABLE Users (name varchar(30), steamprofile varchar(150), user_id varchar(100), region varchar(2))") # create table users

def check_for_connection():
    try:
        users_db.ping(reconnect=True, attempts=1, delay=0)
    except:
        users_db.reconnect(attempts=3, delay=0)

# events
@client.event
async def on_ready():
    print("Bot is ready.")

@client.event
async def on_member_remove(member):
    check_for_connection()

    user_id = str(member.id)
    if get_user_exists(user_id):
        # commit delete query
        cursor.execute("DELETE FROM Users WHERE user_id='" + user_id + "'")
        users_db.commit()

# commands
@client.command(aliases=['jq', 'jQ', 'Jq', 'JQ'])
async def joinqueue(sender):
    check_for_connection()


    if sender.channel.name == "1vs1-queue":
        if sender_in_queue(sender):
            return

        # check if user is registered
        if not get_user_exists(str(sender.author.id)):
            await sender.send("**Error! You must be registered to use this feature! Please visit: ** " + client.get_channel(709746013749117047).mention + " **and** " + client.get_channel(709842720562217012).mention)
            return

        # if sender not already in queue
        queue.append(sender) # add sender to queue
        await alert_queue_interacted(sender, True)
        await handle_matches(sender)
    else:
        await sender.send("**You may only join a queue from: ** " + client.get_channel(709175798807920672).mention)

@client.command(aliases=['lq', 'LQ', 'Lq', 'lQ'])
async def leavequeue(sender):
    check_for_connection()

    if sender.channel.name == "1vs1-queue":
        if not sender_in_queue(sender):
            return

        for i in queue:
            if str(i.author) == str(sender.author):
                queue.remove(i)

        await alert_queue_interacted(sender, False)
    else:
        await sender.send("**You may only leave a queue from: ** " + client.get_channel(709175798807920672).mention)

@client.command()
async def clear(sender, amount=1):
    check_for_connection()

    if "staff" in [role.name.lower() for role in sender.author.roles] or "administrator" in [role.name.lower() for role in sender.author.roles] or "owner" in [role.name.lower() for role in sender.author.roles]:
        await sender.channel.purge(limit=amount + 1)

@client.command()
async def clearall(sender):
    check_for_connection()

    if "staff" in [role.name.lower() for role in sender.author.roles] or "administrator" in [role.name.lower() for role in sender.author.roles] or "owner" in [role.name.lower() for role in sender.author.roles]:
        msg_cnt = 0
        async for msg in sender.channel.history():
            msg_cnt += 1

        await sender.channel.purge(limit=msg_cnt)

@client.command()
async def register(sender):
    check_for_connection()

    if sender.channel.name == "register":
        region = sender.message.content[10:12]
        profilelink = sender.message.content[13:]
        id = str(sender.author.id)
        name = get_pure_name(sender)

        # check for correct syntax
        if (region.lower() == "eu" or region.lower() == "na") and (profilelink[:36] == "https://steamcommunity.com/profiles/" or profilelink[:30] == "https://steamcommunity.com/id/" or profilelink[:35] == "http://steamcommunity.com/profiles/" or profilelink[:29] == "http://steamcommunity.com/id/"): # correct region selection & steamlink
            # check if user already exists
            if not get_user_exists(id):
                # REGISTER USER :
                cursor.execute("INSERT INTO Users (name, steamprofile, user_id, region) VALUES(%s, %s, %s, %s)", (name, profilelink, id, region))
                users_db.commit()
                await sender.send("**Successfuly regsitered user: **" + name) # notify user registration was successful
                print("inserted user: " + name + " to the database!")

                # give member Unranked role
                if not sender.guild.get_role(708951019240947813) in sender.author.roles: # if user doesn't already have role unranked
                    await sender.author.add_roles(sender.guild.get_role(708951019240947813)) # give them role unranked
                    print("Added role Unranked to " + get_pure_name(sender))
            else:
                print("user already exists in the database!")
                await sender.send("**User** " + name + " **Already exists in the system!**") # notify user registration was unsuccessful
        else:
            await sender.send("**Incorrect register syntax. Please visit: **" + client.get_channel(709842720562217012).mention)
            print(profilelink[:30])
    else:
        await sender.send("**To register please visit: **" + client.get_channel(709746013749117047).mention)

@client.command()
async def update(sender):
    check_for_connection()

    if sender.channel.name == "register":
        region = sender.message.content[8:10]
        profilelink = sender.message.content[11:]
        id = str(sender.author.id)
        name = get_pure_name(sender)

        # check for correct syntax
        if (region.lower() == "eu" or region.lower() == "na") and (profilelink[:36] == "https://steamcommunity.com/profiles/" or profilelink[:30] == "https://steamcommunity.com/id/" or profilelink[:35] == "http://steamcommunity.com/profiles/" or profilelink[:29] == "http://steamcommunity.com/id/"): # correct region selection & steamlink
            if get_user_exists(id):
                cursor.execute("UPDATE Users SET region = '" + region + "', steamprofile='" + profilelink + "' WHERE user_id='" + id + "'")
                await sender.send("**Successfuly updated user:** " + name)

            else:
                await sender.send("**You must first be registered to use this feature! To register, please visit: " + client.get_channel(709746013749117047).mention)
        else:
            await sender.send("**Incorrect register syntax. Please visit: **" + client.get_channel(709842720562217012).mention)
    else:
        await sender.send("**To update your information please visit: **" + client.get_channel(709746013749117047).mention)

@client.command(aliases=['sysremove'])
async def sys_remove(sender):
    check_for_connection()

    if sender.channel.name == "staff-commands":
        user_id = sender.message.content[11:]
        user_name = sender.guild.get_member(int(user_id)).name
        if get_user_exists(user_id):
            # commit delete query
            cursor.execute("DELETE FROM Users WHERE user_id='" + user_id + "'")
            users_db.commit()

            # remove roles
            await sender.guild.get_member(int(user_id)).remove_roles(sender.guild.get_role(708951019240947813))
            print("Removed role Unranked from " + user_name)

            print("removed user '" + user_name + "' from the database!")
            await sender.send("**Removed user** " + user_name + " **from the system!**")
        else:
            await sender.send("**Error! This user does not exist in the system!**")

@client.command(aliases=['vd', 'VD', 'vD', 'Vd'])
async def viewdatabase(sender):
    check_for_connection()

    if "owner" in [role.name.lower() for role in sender.author.roles] and sender.channel.name == "owner-commands":
        data = ""
        cursor.execute("SELECT * FROM Users")
        for x in cursor:
            data += str(x) + "\n"
        embed = discord.Embed(thumbnail=None)
        await sender.send(data, embed = embed)

async def alert_queue_interacted(sender, interaction):
    check_for_connection()

    interaction_name = "joined"
    if not interaction:
        interaction_name = "left"

    message = "**" + get_pure_name(sender) + "** has " + interaction_name + " the queue!\n"
    message += "**Current Queue:** " + array_to_string(queue)
    await sender.send(message)

def get_user_exists(id):
    check_for_connection()

    cursor.execute("SELECT name FROM Users WHERE user_id='" + id + "'")
    cnt = 0
    for x in cursor:
        cnt += 1
    return cnt > 0

def array_to_string(arr):
    check_for_connection()

    message = ""
    for i in arr:
        message += get_pure_name(i) + ", "

    message = message[:len(message) - 2] + "."

    if not queue:
        message = ""

    return message

def sender_in_queue(sender):
    check_for_connection()

    for snd in queue:
        if str(snd.author) == str(sender.author):
            return True

    return False

async def handle_matches(context):
    check_for_connection()

    if len(queue) > 1:
        player1 = queue.pop()
        player2 = queue.pop()
        players = [player1, player2]
        player1_steam_profile = ""
        player2_steam_profile = ""
        embed = discord.Embed(thumbnail=None)

        lobby_creator = random.choice(players)
        players.remove(lobby_creator)
        lobby_joiner = players[0]

        # set lobby_creator id
        cursor.execute("SELECT steamprofile FROM Users WHERE user_id='" + str(lobby_creator.author.id) + "'")
        for x in cursor:
            lobby_creator_steam_profile = str(x)[2:len(str(x)) - 3]

        # set lobby_joiner id
        cursor.execute("SELECT steamprofile FROM Users WHERE user_id='" + str(lobby_joiner.author.id) + "'")
        for x in cursor:
            lobby_joiner_steam_profile = str(x)[2:len(str(x)) - 3]

        # alert channel about found match
        match_found_message = "**Match Found:** " + get_pure_name(lobby_creator) + " **VS** " + get_pure_name(lobby_joiner)
        await context.send(match_found_message)

        # alert opponents in private messages
        await lobby_creator.author.send("**--------------------------------------------------------------**\n**A match has been found! _Opponent_:** " + str(lobby_joiner.author) + "\n**Opponent steam profile:** " + lobby_joiner_steam_profile + "\n**You need to make a lobby and wait for your opponent to join in the next 1 - 2 minutes**", embed=embed)
        await lobby_joiner.author.send("**--------------------------------------------------------------**\n**A match has been found! _Opponent_:** " + str(lobby_creator.author) + "\n**Opponent steam profile:** " + lobby_creator_steam_profile + "\n**You need to join your opponent's lobby in the next 1 - 2 minutes**", embed=embed)
        await handle_voice_channel_invite(player1, player2)

def get_pure_name(sender):
    return str(sender.author)[:len(str(sender.author)) - 5]

async def handle_voice_channel_invite(player1, player2):
    check_for_connection()

    #if user is in a voice channel
    if player1.author.voice and player1.author.voice.channel:
        player1_vc = player1.author.voice.channel

        #if channel has free spots
        if len(player1_vc.members) < player1_vc.user_limit:
            link = await player1_vc.create_invite(max_age = 300)
            await player2.author.send("Your opponent is in this voice channel: " + link.url + "\n**--------------------------------------------------------------**")
        else:
            await player2.author.send("Your opponent is in a full voice chat room.")
    else:
        await player2.author.send("Your opponent is currently not in a voice channel.\n**--------------------------------------------------------------**")

    #if user is in a voice channel
    if player2.author.voice and player2.author.voice.channel:
        player2_vc = player2.author.voice.channel

        #if channel has free spots
        if len(player2_vc.members) < player2_vc.user_limit:
            link = await player2_vc.create_invite(max_age = 300)
            await player1.author.send("Your opponent is in this voice channel: " + link.url + "\n**--------------------------------------------------------------**")
        else:
            await player1.author.send("Your opponent is in a full voice chat room.")
    else:
        await player1.author.send("Your opponent is currently not in a voice channel.\n**--------------------------------------------------------------**")

client.run('NzA4OTg4NDc1ODQ3OTk5NTAw.Xrg8hA.S0GNbhEodGmZQmT53z1KKtOKgFQ')
