import discord
import os
import sys
import traceback
import seqlog
import logging
from datetime import datetime

from reminder import try_handle_remind_me, load_reminders
from gym import try_handle_mhm
from reputation import try_handle_bad_bot, try_handle_good_bot, try_handle_reaction_bot, try_handle_greeting
from timeteller import try_handle_risto_time, try_handle_silver_time
from gambling import try_handle_daily, try_handle_bet, try_handle_balance
from instantmeme import try_handle_instant_meme
from ace import try_handle_ace
from impersonate import try_handle_impersonation
from ai import try_handle_ai

seqlog.log_to_seq(
   server_url="http://seq:5341/",
   api_key="5gFywFBgqKr5OzJhvydH",
   level=logging.DEBUG,
   batch_size=10,
   auto_flush_timeout=10,
   override_root_logger=True)

intents = discord.Intents.default()
intents.message_content = True
start_time: datetime = None
client = discord.Client(intents=intents)


async def try_handle_help(message):
    if message.content.startswith('$help'):
        await message.channel.send('KYS')


async def try_handle_uptime(message: discord.Message):
    if message.content.startswith('$uptime'):
        uptime = datetime.now() - start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await message.channel.send(
            f"Ma näen kõwwa vaeva juba: "
            f"{days}d {hours}h {minutes}m {seconds}s\n"
            f"Alates: {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )


@client.event
async def on_ready():
    global start_time
    start_time = datetime.now()

    logging.info(f'We have logged in as {client.user}')
    activity = discord.Activity(type=discord.ActivityType.listening, name="AI-Podcast: Poopoo Peepee")
    await client.change_presence(status=discord.Status.online, activity=activity)
    await load_reminders(client)

    startup_channel_id = int(os.environ.get('STARTUP_CHANNEL', '1297656271092187237'))
    channel = client.get_channel(startup_channel_id)
    if channel:
        await channel.send(f"🔄 PIRRRAAAKIII, ma olen tagasi {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        logging.error(f"Could not find channel with ID {startup_channel_id}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    try:
        await try_handle_uptime(message)

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

        await try_handle_impersonation(client, message)

        await try_handle_greeting(message)

        await try_handle_daily(message)

        await try_handle_bet(message)

        await try_handle_balance(message)

        await try_handle_ai(client, message)

    except Exception:
        logging.exception(traceback.format_exc())
        await message.reply('UPSI WUPSI!! Uwu ma tegin nussi-vussi!! Wäikese kebo bongo! Ergo näeb KÕWA WAEWA, et see ära parandada nii kiiresti kui ta heaks arvab.')

    sys.stdout.flush()


client.run(os.environ.get('TOKEN'))
