import discord
import os
import sys
import traceback

from reminder import tryHandleRemindMe, load_reminders
from gym import tryHandleMhm
from reputation import tryHandleBadBot, tryHandleGoodBot, tryHandleReactionBot
from timeteller import tryHandleRistoTime, tryHandleSilverTime
from instantmeme import tryHandleInstantMeme

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

async def tryHandleHelp(message):
    if message.content.startswith('$help'):
        await message.channel.send('KYS')

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}', flush=True)
    activity = discord.Activity(type=discord.ActivityType.watching, name="feetpics")
    await client.change_presence(status=discord.Status.online, activity=activity)
    await load_reminders(client)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    try:
        await tryHandleMhm(message)

        await tryHandleRemindMe(client, message)

        await tryHandleBadBot(message)

        await tryHandleGoodBot(client, message)

        await tryHandleReactionBot(client, message)

        await tryHandleRistoTime(message)

        await tryHandleSilverTime(message)

        await tryHandleHelp(message)

        await tryHandleInstantMeme(message)

    except Exception:
        print(traceback.format_exc())
        await message.reply('UPSI WUPSI!! Uwu ma tegin nussi-vussi!! Wäikese kebo bongo! Ergo näeb KÕWA WAEWA, et see ära parandada nii kiiresti kui ta heaks arvab.')

    sys.stdout.flush()

client.run(os.environ.get('TOKEN'))
