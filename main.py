import discord
import os
import sys
import traceback
import seqlog
import logging


from reminder import try_handle_remind_me, load_reminders
from gym import try_handle_mhm
from reputation import try_handle_bad_bot, try_handle_good_bot, try_handle_reaction_bot
from timeteller import try_handle_risto_time, try_handle_silver_time
from instantmeme import try_handle_instant_meme
from ace import try_handle_ace

seqlog.log_to_seq(
   server_url="http://seq:5341/",
   api_key="5gFywFBgqKr5OzJhvydH",
   level=logging.DEBUG,
   batch_size=10,
   auto_flush_timeout=10,
   override_root_logger=True)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


async def try_handle_help(message):
    if message.content.startswith('$help'):
        await message.channel.send('KYS')


@client.event
async def on_ready():
    logging.info(f'We have logged in as {client.user}')
    activity = discord.Activity(type=discord.ActivityType.watching, name="feetpics")
    await client.change_presence(status=discord.Status.online, activity=activity)
    await load_reminders(client)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    try:
        await try_handle_mhm(message)

        await try_handle_remind_me(client, message)

        await try_handle_bad_bot(message)

        await try_handle_good_bot(client, message)

        await try_handle_reaction_bot(client, message)

        await try_handle_risto_time(message)

        await try_handle_silver_time(message)

        await try_handle_help(message)

        await try_handle_instant_meme(message)

        await try_handle_ace(message)

    except Exception:
        logging.exception(traceback.format_exc())
        await message.reply('UPSI WUPSI!! Uwu ma tegin nussi-vussi!! Wäikese kebo bongo! Ergo näeb KÕWA WAEWA, et see ära parandada nii kiiresti kui ta heaks arvab.')

    sys.stdout.flush()


client.run(os.environ.get('TOKEN'))
