import discord
import os
import asyncio
import sqlite3
import re
from datetime import datetime, timedelta
import pytz
import requests

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

PROMETHEUS_URL = 'http://prometheus:9090'

# Create or connect to the database
conn = sqlite3.connect('data/reminders.db')
c = conn.cursor()

# Create a table to store reminders if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS reminders (
    user_id INTEGER,
    channel_id INTEGER,
    reminder_message TEXT,
    remind_at DATETIME
)''')
conn.commit()

# Function to convert time with units into seconds
def convert_time_to_seconds(time_str):
    time_regex = r"(\d+)\s*(second|minute|hour|day|month|year)s?"
    match = re.match(time_regex, time_str.lower())

    if not match:
        return None

    value, unit = int(match.group(1)), match.group(2)

    time_multipliers = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400,
        'month': 2592000,  # Assuming 30 days in a month
        'year': 31536000   # 365 days
    }

    return value * time_multipliers.get(unit, 0)

# Function to save a reminder to the database
def save_reminder(user_id, channel_id, message, remind_at):
    c.execute("INSERT INTO reminders (user_id, channel_id, reminder_message, remind_at) VALUES (?, ?, ?, ?)",
              (user_id, channel_id, message, remind_at))
    conn.commit()

# Function to load reminders and resume waiting for them
async def load_reminders():
    c.execute("SELECT rowid, * FROM reminders")
    reminders = c.fetchall()

    for reminder in reminders:
        rowid, user_id, channel_id, message, remind_at = reminder
        remind_at_dt = datetime.strptime(remind_at, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()

        # Calculate remaining time
        remaining_seconds = (remind_at_dt - now).total_seconds()

        if remaining_seconds > 0:
            # If time is still in the future, set a task to wait for it
            asyncio.create_task(schedule_reminder(rowid, user_id, channel_id, message, remaining_seconds))
        else:
            # If the reminder time has already passed, send the reminder immediately
            await send_reminder(rowid, user_id, channel_id, message)

# Function to wait and send the reminder
async def schedule_reminder(rowid, user_id, channel_id, message, wait_time):
    await asyncio.sleep(wait_time)
    await send_reminder(rowid, user_id, channel_id, message)

# Function to send the reminder
async def send_reminder(rowid, user_id, channel_id, message):
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(f"<@{user_id}>, reminder: {message}")

    # Delete reminder from database after sending
    c.execute("DELETE FROM reminders WHERE rowid = ?", (rowid,))
    conn.commit()

def round_time_to_nearest_quarter_hour(dt=None):
    if dt is None:
        dt = datetime.utcnow()
    # Zero out the seconds and microseconds
    dt = dt.replace(second=0, microsecond=0)
    minute = (dt.minute // 15) * 15
    remainder = dt.minute % 15
    if dt.minute % 15 >= 8:
        minute += 15
    if minute >= 60:
        minute = 0
        dt += timedelta(hours=1)
    dt = dt.replace(minute=minute)
    return dt

def get_same_weekday_dates(current_date, weeks_back=2):
    dates = []
    for i in range(1, weeks_back+1):
        date = current_date - timedelta(weeks=i)
        dates.append(date)
    return dates

def get_max_people_count_for_day(date):
    try:
        start_time = datetime.combine(date, datetime.min.time()).timestamp()
        end_time = datetime.combine(date + timedelta(days=1), datetime.min.time()).timestamp()
        query = 'sum(max_over_time(people_count[1d]))'
        params = {
            'query': query,
            'start': start_time,
            'end': end_time,
            'step': '1d',
        }
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params=params)
        data = response.json()
        if data['status'] == 'success' and len(data['data']['result'])==1:
            return int(data['data']['result'][0]['value'][1])
        return 0
    except Exception as e:
        print(f"Error fetching data for date {date}: {e}")
        return 0

def get_average_people_count_at_time(time):
    try:
        timestamp = time.timestamp()
        query = 'sum(people_count)'
        params = {
            'query': query,
            'time': timestamp,
        }
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params=params)
        data = response.json()
        if data['status'] == 'success' and len(data['data']['result'])==1:
            return int(data['data']['result'][0]['value'][1])
        return 0
    except Exception as e:
        print(f"Error fetching average people count at time {time}: {e}")
        return 0


async def tryHandleMhm(message):
    if 'mhm' not in message.content.lower():
        return
    
    current_time = round_time_to_nearest_quarter_hour()
    current_date = current_time.date()
    dates = get_same_weekday_dates(current_date)

    current_counts = []
    daily_maxima = []
    for date in dates:
        max_count = get_max_people_count_for_day(date)
        daily_maxima.append(max_count)
        current_count = get_average_people_count_at_time(current_time)
        current_counts.append(current_count)
    
    average_daily_max = sum(daily_maxima) / len(daily_maxima)
    average_daily_current = sum(current_counts) / len(current_counts)

    percentage = average_daily_current / average_daily_max

    if(percentage > 0.5):
        await message.reply(f'Ta pigem on jõuksis! (ratio={percentage:.2f})')
    else:
        await message.reply(f'Ta pigem pole jõuksis! (ratio={percentage:.2f})')
    

async def tryHandleRemindMe(message):
    if message.content.startswith('$remindme'):
        try:
            # Example format: $remindme "Your reminder message" 3 days
            command_pattern = r'\$remindme\s*"(.+)"\s*(\d+\s*\w+)'
            match = re.match(command_pattern, message.content)

            if not match:
                await message.channel.send("Please use the correct format: $remindme \"your message\" time (e.g., 3 days).")
                return

            reminder_message = match.group(1)
            time_str = match.group(2)

            # Convert time string to seconds
            time_in_seconds = convert_time_to_seconds(time_str)
            if time_in_seconds is None:
                await message.channel.send("Invalid time format! Use a number followed by a unit (seconds, minutes, hours, days, months, or years).")
                return

            # Calculate when the reminder should be triggered
            remind_at = datetime.now() + timedelta(seconds=time_in_seconds)

            # Save the reminder to the database
            save_reminder(message.author.id, message.channel.id, reminder_message, remind_at.strftime('%Y-%m-%d %H:%M:%S'))

            # Set a task to wait and send the reminder
            asyncio.create_task(schedule_reminder(None, message.author.id, message.channel.id, reminder_message, time_in_seconds))

            await message.channel.send(f"Reminder set! I'll remind you to \"{reminder_message}\" in {time_str}.")

        except Exception as e:
            await message.channel.send(f"Something went wrong: {str(e)}")

async def tryHandleSilverTime(message):
    if message.content.startswith('$silvertime'):
        sydney_timezone = pytz.timezone('Australia/Sydney')
        sydney_time = datetime.now(sydney_timezone)
        await message.channel.send(f"Time in Sydney, Australia is {sydney_time.strftime('%H:%M')}")

async def tryHandleRistoTime(message):
    if message.content.startswith('$ristotime'):
        ams_tz = pytz.timezone('Europe/Amsterdam')
        ams_time = datetime.now(ams_tz)
        await message.channel.send(f"Time in Maaskantje, Netherlands is {ams_time.strftime('%H:%M')}")

async def tryHandleBadBot(message):
    if "bad bot" in message.content.lower():
        await message.add_reaction('😢')

async def tryHandleGoodBot(message):
    if "good bot" in message.content.lower():
        emoji = client.get_emoji(1291820499420053677)
        await message.add_reaction(emoji)

async def tryHandleHelp(message):
    if message.content.startswith('$help'):
        await message.channel.send('KYS')

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await load_reminders()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    try:
        await tryHandleMhm(message)
        
        await tryHandleRemindMe(message)

        await tryHandleBadBot(message)

        await tryHandleGoodBot(message)

        await tryHandleRistoTime(message)

        await tryHandleSilverTime(message)

        await tryHandleHelp(message)
    except Exception as e:
        message.reply('UPSI WUPSI!! Uwu ma tegin nussi-vussi!! Wäikese kebo bongo! Ergo näeb KÕWA WAEWA, et see ära parandada nii kiiresti kui ta heaks arvab.')

client.run(os.environ.get('TOKEN'))
